# HeadLight to ODOT PDF Converter

A web application that converts HeadLight JSON exports to ODOT (Oregon Department of Transportation) PDF forms.

## Features

- **JSON Import**: Upload HeadLight JSON export files
- **Automatic Mapping**: Maps HeadLight data to ODOT form fields including:
  - Weather conditions and temperature ranges
  - Personnel and contractor information
  - Equipment details
  - Work items and quantities
  - Photos and remarks
- **PDF Generation**: Creates fillable ODOT PDF forms
- **Photo Upload**: Upload additional photos to include in the report

## How to Use

1. **Upload HeadLight JSON**: Select your HeadLight JSON export file
2. **Upload Photos (Optional)**: Add any additional photos you want to include
3. **Convert**: Click "Convert to ODOT PDF" to generate the form
4. **Download**: Download the completed ODOT PDF form

## Live Demo

This application is hosted on Streamlit: [https://headlight-odot-converter.streamlit.app](https://headlight-odot-converter.streamlit.app)

## Technical Details

- **Backend**: FastAPI with Python
- **Frontend**: HTML/JavaScript
- **PDF Processing**: pikepdf library
- **Hosting**: Streamlit Cloud

## Data Mapping

The application automatically maps:
- Weather data to appropriate ODOT weather categories
- Personnel data to contractor and trade categories
- Equipment information to equipment sections
- Work items to quantity and location fields
- Photos to the photographs section
- Narrative data to remarks sections

## Support

For technical support or questions, please contact the development team.