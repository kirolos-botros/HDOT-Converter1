import json
from typing import Dict, List, Any, Optional
from pathlib import Path
import io
import pytz
from datetime import datetime
from pikepdf import Pdf, Name, Dictionary, Array, Stream
from PIL import Image
import os

class HeadLightToODOTConverter:
    def __init__(self, odot_template_path: str):
        self.odot_template_path = odot_template_path
        self._radio_button_counters = {}
        
    def extract_equipment_data(self, data: Dict[str, Any]) -> str:
        """Extract equipment data from HeadLight JSON"""
        equipment_list = []
        
        # Look for equipment in various sections
        if 'Equipment' in data:
            for item in data['Equipment']:
                if isinstance(item, dict):
                    name = item.get('Name', '')
                    if name:
                        equipment_list.append(name)
        
        # Also check for equipment in other sections
        if 'DailyReport' in data:
            daily_report = data['DailyReport']
            if 'Equipment' in daily_report:
                for item in daily_report['Equipment']:
                    if isinstance(item, dict):
                        name = item.get('Name', '')
                        if name:
                            equipment_list.append(name)
        
        return '\n'.join(equipment_list) if equipment_list else ''
    
    def extract_remarks_data(self, data: Dict[str, Any]) -> str:
        """Extract remarks/narrative data from HeadLight JSON"""
        remarks_list = []
        
        # Look for narrative/remarks in various sections
        if 'Narrative' in data:
            narrative = data['Narrative']
            if isinstance(narrative, list):
                for item in narrative:
                    if isinstance(item, dict):
                        text = item.get('Text', '')
                        timestamp = item.get('Timestamp', '')
                        if text:
                            if timestamp:
                                remarks_list.append(f"[{timestamp}] {text}")
                            else:
                                remarks_list.append(text)
            elif isinstance(narrative, str):
                remarks_list.append(narrative)
        
        # Also check for remarks in other sections
        if 'DailyReport' in data:
            daily_report = data['DailyReport']
            if 'Narrative' in daily_report:
                narrative = daily_report['Narrative']
                if isinstance(narrative, list):
                    for item in narrative:
                        if isinstance(item, dict):
                            text = item.get('Text', '')
                            timestamp = item.get('Timestamp', '')
                            if text:
                                if timestamp:
                                    remarks_list.append(f"[{timestamp}] {text}")
                                else:
                                    remarks_list.append(text)
                elif isinstance(narrative, str):
                    remarks_list.append(narrative)
        
        return '\n'.join(remarks_list) if remarks_list else ''
    
    def extract_classification(self, data: Dict[str, Any]) -> str:
        """Extract classification from HeadLight JSON"""
        if 'Inspector' in data:
            inspector = data['Inspector']
            if isinstance(inspector, dict):
                return inspector.get('Classification', '')
            elif isinstance(inspector, list) and len(inspector) > 0:
                return inspector[0].get('Classification', '')
        return ''
    
    def extract_superintendent_name(self, data: Dict[str, Any]) -> str:
        """Extract the name of the person with 'Superintendent' trade"""
        if 'Personnel' in data:
            personnel = data['Personnel']
            if isinstance(personnel, list):
                for person in personnel:
                    if isinstance(person, dict):
                        trade = person.get('Trade', '')
                        name = person.get('Name', '')
                        if trade and 'Superintendent' in trade and name:
                            return name
        return ''
    
    def extract_weather_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process weather data from HeadLight JSON"""
        weather_data = {
            'temperature': 0,
            'wind': 'Calm',
            'humidity': 50,  # Default to 50% as a number
            'conditions': 'Clear'
        }
        
        if 'Weather' in data:
            weather = data['Weather']
            if isinstance(weather, dict):
                # Temperature
                temp = weather.get('Temperature', 0)
                if temp:
                    weather_data['temperature'] = float(temp) if isinstance(temp, str) else temp
                
                # Wind
                wind = weather.get('Wind', 'Calm')
                if wind:
                    weather_data['wind'] = wind
                
                # Humidity - handle both numeric and text values
                humidity = weather.get('Humidity', 50)
                
                # If humidity is a string, map it to a percentage
                if isinstance(humidity, str):
                    humidity_lower = humidity.lower()
                    if 'dry' in humidity_lower:
                        humidity = 25
                    elif 'low' in humidity_lower:
                        humidity = 35
                    elif 'medium' in humidity_lower or 'med' in humidity_lower:
                        humidity = 60
                    elif 'high' in humidity_lower:
                        humidity = 80
                    else:
                        humidity = 50  # Default
                else:
                    # If it's already a number, use it
                    humidity = float(humidity) if humidity else 50
                
                weather_data['humidity'] = humidity
                
                # Conditions
                conditions = weather.get('Conditions', 'Clear')
                if conditions:
                    weather_data['conditions'] = conditions
        
        return weather_data
    
    def get_day_of_week(self, date_str: str, timezone_str: str = 'America/Los_Angeles') -> str:
        """Get day of week from date string, handling timezone conversion"""
        try:
            # Parse the date string
            if 'T' in date_str:
                # ISO format with time
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Date only format
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            
            # If timezone is specified, convert to local timezone
            if timezone_str and 'T' in date_str:
                try:
                    tz = pytz.timezone(timezone_str)
                    # If the datetime is naive, assume it's UTC
                    if dt.tzinfo is None:
                        dt = pytz.UTC.localize(dt)
                    # Convert to local timezone
                    dt = dt.astimezone(tz)
                except:
                    # If timezone conversion fails, use the original datetime
                    pass
            
            # Get day of week
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            return days[dt.weekday()]
        except:
            return 'Monday'  # Default fallback
    
    def create_field_mapping(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mapping from HeadLight data to ODOT form fields"""
        field_mapping = {}
        
        # Extract basic data
        work_date = data.get('DocumentDate', '')
        timezone = data.get('Timezone', 'America/Los_Angeles')
        day_of_week = self.get_day_of_week(work_date, timezone)
        
        # Format date for display
        try:
            if 'T' in work_date:
                dt = datetime.fromisoformat(work_date.replace('Z', '+00:00'))
                if timezone:
                    try:
                        tz = pytz.timezone(timezone)
                        if dt.tzinfo is None:
                            dt = pytz.UTC.localize(dt)
                        dt = dt.astimezone(tz)
                    except:
                        pass
                formatted_date = dt.strftime('%m/%d/%y')
            else:
                dt = datetime.strptime(work_date, '%Y-%m-%d')
                formatted_date = dt.strftime('%m/%d/%y')
        except:
            formatted_date = work_date
        
        # Weather data
        weather = self.extract_weather_data(data)
        
        # Temperature mapping - ensure it's a number
        temp = weather['temperature']
        temp_float = float(temp) if isinstance(temp, str) else temp
        
        if temp_float >= 83:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row2[0].Cell1[0]'] = '/Yes'
        elif temp_float >= 70:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row2[0].Cell2[0]'] = '/Yes'
        elif temp_float >= 50:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row2[0].Cell3[0]'] = '/Yes'
        elif temp_float >= 32:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row2[0].Cell4[0]'] = '/Yes'
        else:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row2[0].Cell5[0]'] = '/Yes'
        
        # Wind mapping
        wind = weather['wind'].lower()
        if 'strong' in wind or 'high' in wind:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row3[0].Cell3[0]'] = '/Yes'
        elif 'moderate' in wind or 'medium' in wind:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row3[0].Cell2[0]'] = '/Yes'
        else:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row3[0].Cell1[0]'] = '/Yes'
        
        # Humidity mapping - humidity is already a number from extract_weather_data
        humidity = weather['humidity']
        
        if humidity >= 75:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row4[0].Cell4[0]'] = '/Yes'
        elif humidity >= 50:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row4[0].Cell3[0]'] = '/Yes'
        elif humidity >= 25:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row4[0].Cell2[0]'] = '/Yes'
        else:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row4[0].Cell1[0]'] = '/Yes'
        
        # Weather conditions mapping
        conditions = weather['conditions'].lower()
        if 'rain' in conditions or 'shower' in conditions:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row1[0].Cell4[0]'] = '/Yes'
        elif 'snow' in conditions:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row1[0].Cell5[0]'] = '/Yes'
        elif 'cloudy' in conditions or 'overcast' in conditions:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row1[0].Cell3[0]'] = '/Yes'
        elif 'fair' in conditions or 'partly' in conditions:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row1[0].Cell2[0]'] = '/Yes'
        else:
            field_mapping['form1[0].Page1[0].WeatherSub[0].Weather[0].Row1[0].Cell1[0]'] = '/Yes'
        
        # Personnel data
        if 'Personnel' in data:
            personnel = data['Personnel']
            if isinstance(personnel, list):
                # Aggregate by contractor
                contractor_totals = {}
                trade_totals = {}
                
                for person in personnel:
                    if isinstance(person, dict):
                        contractor = person.get('Contractor', '')
                        trade = person.get('Trade', '')
                        count = person.get('Count', 1)
                        
                        if not contractor:
                            continue
                        
                        # Initialize contractor totals
                        if contractor not in contractor_totals:
                            contractor_totals[contractor] = 8  # Fixed 8 hours if any personnel present
                        
                        # Map trade to column
                        trade_column_mapping = {
                            'Supervisor': 1,
                            'Superintendent': 1,  # Map Superintendent to Supervisors
                            'Operator': 2,
                            'Truck Driver': 3,
                            'Laborer': 4
                        }
                        
                        # Handle blank/empty trades as Laborers
                        if not trade or trade.strip() == '':
                            trade = 'Laborer'
                        
                        # Get column for this trade
                        if trade in trade_column_mapping:
                            col = trade_column_mapping[trade]
                        else:
                            # Auto-create new columns for new trades
                            max_col = max(trade_column_mapping.values()) if trade_column_mapping else 4
                            trade_column_mapping[trade] = max_col + 1
                            col = max_col + 1
                        
                        # Sum counts by trade
                        if trade not in trade_totals:
                            trade_totals[trade] = 0
                        trade_totals[trade] += count
                
                # Map contractor totals to left table
                row = 0
                for contractor, hours in contractor_totals.items():
                    if row < 10:  # Limit to 10 rows
                        field_mapping[f'form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].ContractorTable[0].Row{row}[0].Cell1[0]'] = contractor
                        field_mapping[f'form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].ContractorTable[0].Row{row}[0].Cell2[0]'] = str(hours)
                        row += 1
                
                # Map trade totals to right table
                for trade, count in trade_totals.items():
                    col = trade_column_mapping.get(trade, 4)
                    if col <= 10:  # Limit to 10 columns
                        field_mapping[f'form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].PersonnelTable1[0].Row2[0].Cell{col}[0]'] = str(count)
        
        # Work items
        if 'WorkItems' in data:
            work_items = data['WorkItems']
            if isinstance(work_items, list):
                for i, item in enumerate(work_items):
                    if isinstance(item, dict) and i < 20:  # Limit to 20 items
                        description = item.get('Description', '')
                        quantity = item.get('Quantity', 0)
                        units = item.get('Units', '')
                        location = item.get('Location', '')
                        
                        # Extract item number from description (e.g., "0010: MOBILIZATION" -> "0010")
                        item_no = ''
                        if ':' in description:
                            item_no = description.split(':')[0].strip()
                            description = description.split(':', 1)[1].strip()
                        
                        # Format total
                        total = f"{quantity} {units}" if quantity and units else str(quantity) if quantity else ''
                        
                        # Map to form fields
                        field_mapping[f'form1[0].Page1[0].TableSub2[0].Place[0].LocationTable1[0].Row{i}[0].Cell1[0]'] = location
                        field_mapping[f'form1[0].Page1[0].TableSub2[0].Place[0].LocationTable1[0].Row{i}[0].Cell2[0]'] = item_no
                        field_mapping[f'form1[0].Page1[0].TableSub2[0].Place[0].LocationTable1[0].Row{i}[0].Cell3[0]'] = total
                        field_mapping[f'form1[0].Page1[0].TableSub2[0].Place[0].LocationTable1[0].Row{i}[0].Cell4[0]'] = description
        
        # Superintendent mapping to On-Site Supervisor
        superintendent_name = self.extract_superintendent_name(data)
        if superintendent_name:
            field_mapping['form1[0].Page1[0].ProjectSub[0].#area[0].Contractor[1]'] = superintendent_name
            # Check "Yes" for Supervisor Present
            field_mapping['form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].PhotoYes[0]'] = True
            field_mapping['form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].PhotoNo[0]'] = False
        else:
            # Check "No" for Supervisor Present
            field_mapping['form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].PhotoYes[0]'] = False
            field_mapping['form1[0].Page1[0].TableSub1[0].Table1[0].PersGroup[0].PhotoNo[0]'] = True
        
        # Classification mapping to Cert No.
        classification = self.extract_classification(data)
        if classification:
            for page_num in range(3):  # Pages 1, 2, 3
                field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].CertNo[0]'] = classification
        
        # Remarks mapping
        remarks = self.extract_remarks_data(data)
        if remarks:
            field_mapping['form1[0].#subform[1].RemarksSub1[0].Remarks[0]'] = remarks
        
        # Equipment mapping
        equipment = self.extract_equipment_data(data)
        if equipment:
            field_mapping['form1[0].Page1[0].EquipSub1[0].Equip[0]'] = equipment
        
        # Footer fields (WorkDate, Shift, PreparedBy, CertNo, Signature) for all pages
        for page_num in range(3):  # Pages 1, 2, 3
            field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].WorkDate[0]'] = formatted_date
            field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].Shift[0]'] = 'Day'
            field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].PreparedBy[0]'] = 'Admin HHPR'
            field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].CertNo[0]'] = classification
            field_mapping[f'form1[0].#pageSet[0].Master1[{page_num}].SignSub[0].#area[0].Signature[0]'] = ''
        
        # Day of week radio buttons
        field_mapping['day_of_week'] = day_of_week
        
        return field_mapping
    
    def fill_pdf_form(self, field_mapping: Dict[str, Any], uploaded_photos: List[Any] = None) -> bytes:
        """Fill the ODOT PDF form with the mapped data"""
        # Reset radio button counters for each new PDF generation
        self._radio_button_counters = {}
        
        pdf = Pdf.open(self.odot_template_path)
        
        # Appearance map for radio buttons (based on template inspection)
        appearance_map = {
            'Monday': '/1',
            'Tuesday': '/2', 
            'Wednesday': '/3',
            'Thursday': '/4',
            'Friday': '/5',
            'Saturday': '/6',
            'Sunday': '/7'
        }
        
        # Fill form fields
        for field_name, value in field_mapping.items():
            if field_name == 'day_of_week':
                continue  # Handle day of week separately
                
            # Find the field in page annotations
            for page in pdf.pages:
                if '/Annots' in page:
                    for annot in page['/Annots']:
                        annot_obj = annot.get_object()
                        if '/T' in annot_obj and '/FT' in annot_obj:
                            field_type = annot_obj['/FT']
                            field_title = annot_obj['/T']
                            
                            if field_title == field_name:
                                if field_type == '/Tx':  # Text field
                                    annot_obj['/V'] = str(value)
                                elif field_type == '/Btn':  # Button/Checkbox
                                    if value is True or value == '/Yes' or value == 'Yes':
                                        annot_obj['/V'] = '/Yes'
                                        annot_obj['/AS'] = '/Yes'
                                    else:
                                        annot_obj['/V'] = '/Off'
                                        annot_obj['/AS'] = '/Off'
                                elif field_type == '/Sig':  # Signature field
                                    annot_obj['/V'] = str(value)
        
        # Handle day of week radio buttons
        day_of_week = field_mapping.get('day_of_week', 'Monday')
        target_appearance = appearance_map.get(day_of_week, '/1')
        
        for page in pdf.pages:
            if '/Annots' in page:
                for annot in page['/Annots']:
                    annot_obj = annot.get_object()
                    if '/T' in annot_obj and '/FT' in annot_obj:
                        field_type = annot_obj['/FT']
                        field_title = annot_obj['/T']
                        
                        if field_type == '/Btn' and 'Day' in field_title:
                            # This is a day of week radio button
                            if field_title not in self._radio_button_counters:
                                self._radio_button_counters[field_title] = 0
                            
                            self._radio_button_counters[field_title] += 1
                            
                            # Check if this is the target day
                            if day_of_week in field_title:
                                annot_obj['/V'] = f'/{day_of_week}'
                                annot_obj['/AS'] = target_appearance
                            else:
                                annot_obj['/V'] = '/Off'
                                annot_obj['/AS'] = '/Off'
        
        # Embed images if provided
        if uploaded_photos:
            self._embed_images_in_pdf(pdf, uploaded_photos)
        
        # Save to bytes
        output = io.BytesIO()
        pdf.save(output)
        return output.getvalue()
    
    def _embed_images_in_pdf(self, pdf: Pdf, uploaded_photos: List[Any]):
        """Embed uploaded images into the PDF on the photographs page"""
        if not uploaded_photos:
            return
        
        # Target page 4 (index 3) for photographs
        target_page = pdf.pages[3]
        
        # Image coordinates from the template (6 PhotoImage fields)
        image_coords = [
            (21.6, 573.2, 189, 142),   # Photo 1: top left
            (324.0, 573.4, 189, 142),  # Photo 2: top right
            (21.6, 348.4, 189, 142),   # Photo 3: middle left
            (324.0, 347.8, 189, 142),  # Photo 4: middle right
            (21.6, 126.4, 189, 142),   # Photo 5: bottom left
            (324.0, 126.4, 189, 142)   # Photo 6: bottom right
        ]
        
        for i, photo in enumerate(uploaded_photos):
            if i >= 6:  # Limit to 6 images
                break
            
            try:
                # Read image data
                image_data = photo.read()
                photo.seek(0)  # Reset file pointer
                
                # Open image with Pillow
                image = Image.open(io.BytesIO(image_data))
                
                # Convert to RGB if necessary
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Get coordinates and dimensions
                x, y, width, height = image_coords[i]
                
                # Resize image to fit the field dimensions
                image.thumbnail((width, height), Image.Resampling.LANCZOS)
                
                # Convert to bytes
                img_buffer = io.BytesIO()
                image.save(img_buffer, format='JPEG', quality=85)
                img_data = img_buffer.getvalue()
                
                # Create PDF XObject
                xobj_name = f'Photo{i+1}'
                xobj = Stream(pdf, img_data)
                xobj['/Type'] = Name('/XObject')
                xobj['/Subtype'] = Name('/Image')
                xobj['/Width'] = image.width
                xobj['/Height'] = image.height
                xobj['/ColorSpace'] = Name('/DeviceRGB')
                xobj['/BitsPerComponent'] = 8
                xobj['/Filter'] = Name('/DCTDecode')
                
                # Add to page resources
                if '/Resources' not in target_page:
                    target_page['/Resources'] = Dictionary()
                if '/XObject' not in target_page['/Resources']:
                    target_page['/Resources']['/XObject'] = Dictionary()
                
                target_page['/Resources']['/XObject'][xobj_name] = xobj
                
                # Create content stream to draw the image
                content_stream = f"""
q
{width} 0 0 {height} {x} {y} cm
/{xobj_name} Do
Q
"""
                
                # Get existing content
                if '/Contents' in target_page:
                    existing_content = target_page['/Contents']
                    if isinstance(existing_content, Array):
                        # Multiple content streams
                        new_stream = Stream(pdf, content_stream.encode())
                        existing_content.append(new_stream)
                    else:
                        # Single content stream
                        existing_content_data = existing_content.read_bytes()
                        combined_content = existing_content_data + content_stream.encode()
                        new_stream = Stream(pdf, combined_content)
                        target_page['/Contents'] = new_stream
                else:
                    # No existing content
                    new_stream = Stream(pdf, content_stream.encode())
                    target_page['/Contents'] = new_stream
                    
            except Exception as e:
                print(f"Error embedding image {i+1}: {e}")
                continue
