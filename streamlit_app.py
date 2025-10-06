import streamlit as st
import json
import tempfile
import os
from converter import HeadLightToODOTConverter
from typing import List, Dict
import io

# Set page config
st.set_page_config(
    page_title="HeadLight to ODOT Converter",
    page_icon="🚧",
    layout="wide"
)

# Title and description
st.title("🚧 HeadLight to ODOT PDF Converter")
st.markdown("""
Convert your HeadLight JSON exports to ODOT (Oregon Department of Transportation) PDF forms.
Upload your HeadLight JSON file and any additional photos to generate a complete ODOT report.
""")

# Initialize the converter
@st.cache_resource
def get_converter():
    return HeadLightToODOTConverter("ODOT Template.pdf")

converter = get_converter()

# Create two columns for file uploads
col1, col2 = st.columns(2)

with col1:
    st.subheader("📄 HeadLight JSON File")
    json_file = st.file_uploader(
        "Upload your HeadLight JSON export",
        type=['json'],
        help="Select the JSON file exported from HeadLight"
    )

with col2:
    st.subheader("📸 Additional Photos (Optional)")
    photo_files = st.file_uploader(
        "Upload photos to include in the report",
        type=['jpg', 'jpeg', 'png', 'gif', 'bmp'],
        accept_multiple_files=True,
        help="Upload any additional photos you want to include in the ODOT report"
    )

# Convert button
if st.button("🔄 Convert to ODOT PDF", type="primary", disabled=json_file is None):
    if json_file is not None:
        try:
            # Show progress
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Read JSON file
            status_text.text("Reading HeadLight JSON file...")
            progress_bar.progress(20)
            
            json_content = json_file.read()
            headlight_data = json.loads(json_content)
            
            # Process photos if any
            uploaded_photos = []
            if photo_files:
                status_text.text("Processing uploaded photos...")
                progress_bar.progress(40)
                
                for photo_file in photo_files:
                    uploaded_photos.append(photo_file)
            
            # Convert to ODOT PDF
            status_text.text("Converting to ODOT PDF...")
            progress_bar.progress(60)
            
            # Create field mapping and fill PDF
            field_mapping = converter.create_field_mapping(headlight_data)
            pdf_bytes = converter.fill_pdf_form(field_mapping, uploaded_photos)
            
            progress_bar.progress(100)
            status_text.text("✅ Conversion complete!")
            
            # Provide download button
            st.success("🎉 ODOT PDF generated successfully!")
            st.download_button(
                label="📥 Download ODOT PDF",
                data=pdf_bytes,
                file_name=f"ODOT_Report_{json_file.name.replace('.json', '')}.pdf",
                mime="application/pdf"
            )
            
            # Show some stats
            st.info(f"📊 Generated PDF with {len(uploaded_photos)} photos and HeadLight data from {json_file.name}")
            
        except Exception as e:
            st.error(f"❌ Error converting file: {str(e)}")
            st.exception(e)
    else:
        st.warning("⚠️ Please upload a HeadLight JSON file first.")

# Add some helpful information
st.markdown("---")
st.markdown("### 📋 How to Use")
st.markdown("""
1. **Export from HeadLight**: Export your daily report as JSON from HeadLight
2. **Upload JSON**: Select the JSON file using the file uploader above
3. **Add Photos (Optional)**: Upload any additional photos you want to include
4. **Convert**: Click the "Convert to ODOT PDF" button
5. **Download**: Download the generated ODOT PDF form

### 🔧 What Gets Mapped
- **Weather Data**: Temperature, wind, humidity, and conditions
- **Personnel**: Contractor information and trade categories
- **Equipment**: Equipment types, amounts, and status
- **Work Items**: Quantities, locations, and descriptions
- **Photos**: All uploaded images
- **Remarks**: Narrative data from HeadLight
""")

# Footer
st.markdown("---")
st.markdown("Built with ❤️ for construction project management")
