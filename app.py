import streamlit as st
from PIL import Image
from PIL.ExifTags import TAGS
import io
import os
import datetime
import magic
import sys
from pathlib import Path

def get_file_metadata(uploaded_file):
    """Get basic file metadata"""
    file_metadata = {
        "File Name": uploaded_file.name,
        "File Size": f"{uploaded_file.size / 1024:.2f} KB",
        "File Type": uploaded_file.type,
        "Last Modified": datetime.datetime.fromtimestamp(
            uploaded_file.getvalue().__sizeof__()
        ).strftime("%Y-%m-%d %H:%M:%S"),
    }
    return file_metadata

def get_image_metadata(image):
    """Get basic image metadata"""
    image_metadata = {
        "Image Format": image.format,
        "Image Mode": image.mode,
        "Image Size": f"{image.width} x {image.height} pixels",
        "Color Depth": f"{image.bits} bits" if hasattr(image, 'bits') else "N/A",
        "DPI": image.info.get('dpi', 'N/A'),
    }
    return image_metadata

def get_exif_data(image):
    """Extract all EXIF data from an image"""
    exif_data = {}
    try:
        # Get the EXIF data from the image
        exif = image._getexif()
        if exif is not None:
            for tag_id in exif:
                tag = TAGS.get(tag_id, tag_id)
                data = exif.get(tag_id)
                
                # Handle different data types
                if isinstance(data, bytes):
                    try:
                        data = data.decode('utf-8')
                    except UnicodeDecodeError:
                        data = data.hex()
                elif isinstance(data, tuple) and len(data) == 2:
                    # Handle rational numbers
                    data = f"{data[0]}/{data[1]}"
                
                exif_data[tag] = data
    except Exception as e:
        st.error(f"Error reading EXIF data: {str(e)}")
    return exif_data

def get_all_image_info(image):
    """Get all available image information"""
    info = {}
    for key, value in image.info.items():
        if isinstance(value, bytes):
            try:
                value = value.decode('utf-8')
            except UnicodeDecodeError:
                value = value.hex()
        info[key] = value
    return info

def main():
    st.set_page_config(
        page_title="ExifExplorer",
        page_icon="📷",
        # layout="wide",
    )

    st.title("📷 ExifExplorer")
    st.write("Upload an image to view all available EXIF Data & Metadata")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose an image file", 
        type=['jpg', 'jpeg', 'png', 'tiff', 'bmp', 'gif', 'webp']
    )

    if uploaded_file is not None:
        try:
            # Create columns for layout
            col1, col2 = st.columns([1, 2])

            # Read the image
            image_bytes = uploaded_file.read()
            image = Image.open(io.BytesIO(image_bytes))
            
            with col1:
                st.image(image, caption="Uploaded Image", use_column_width=True)
                
                # Display file metadata
                st.subheader("File Information")
                file_meta = get_file_metadata(uploaded_file)
                for key, value in file_meta.items():
                    st.write(f"**{key}:** {value}")

            with col2:
                # Create tabs for different types of metadata
                tab1, tab2, tab3 = st.tabs([
                    "Image Properties", 
                    "EXIF Data",
                    "Additional Metadata"
                ])

                # Tab 1: Basic Image Properties
                with tab1:
                    st.subheader("Basic Image Properties")
                    image_meta = get_image_metadata(image)
                    for key, value in image_meta.items():
                        st.write(f"**{key}:** {value}")

                # Tab 2: EXIF Data
                with tab2:
                    st.subheader("EXIF Metadata")
                    exif_data = get_exif_data(image)
                    if exif_data:
                        # Group EXIF data by categories
                        categories = {
                            "Camera": ["Make", "Model", "Software", "LensMake", "LensModel"],
                            "Capture": ["DateTimeOriginal", "ExposureTime", "FNumber", "ISOSpeedRatings", 
                                      "FocalLength", "ExposureProgram", "Flash"],
                            "Image": ["ImageWidth", "ImageLength", "BitsPerSample", "Compression", 
                                    "PhotometricInterpretation", "Orientation"],
                            "Location": ["GPSInfo", "GPSLatitude", "GPSLongitude", "GPSAltitude"],
                            "Other": []
                        }

                        # Create expanders for each category
                        for category, tags in categories.items():
                            with st.expander(f"{category} Information", expanded=True):
                                found_data = False
                                for tag, value in exif_data.items():
                                    if tag in tags or (category == "Other" and not any(tag in cat_tags for cat_tags in categories.values())):
                                        st.write(f"**{tag}:** {value}")
                                        found_data = True
                                if not found_data:
                                    st.write("No data available")
                    else:
                        st.info("No EXIF data found in the image.")

                # Tab 3: Additional Metadata
                with tab3:
                    st.subheader("Additional Metadata")
                    additional_meta = get_all_image_info(image)
                    if additional_meta:
                        for key, value in additional_meta.items():
                            if key not in exif_data:
                                st.write(f"**{key}:** {value}")
                    else:
                        st.info("No additional metadata found")

        except Exception as e:
            st.error(f"Error processing image: {str(e)}")
            st.error("Stack trace:", exc_info=True)

if __name__ == "__main__":
    main()