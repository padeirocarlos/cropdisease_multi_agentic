import os
import json
import base64
import qrcode
import requests
import mimetypes
from PIL import Image
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from qrcode.image.styledpil import StyledPilImage

load_dotenv(override=True)

mcp = FastMCP(name="filesystem-mcp-server")

@mcp.resource("config://app-version")
def get_app_version() -> dict:
    """Static resource providing application version information"""
    return {
        "name": "filesystem-mcp-server",
        "version": "1.0.0",
        "release_date": "2025-10-15",
        "environment": "production"
    }
    
@mcp.tool()
def read_file(path: str) -> str:
    """Read contents of a file.
    
    Args:
        path: Path to the file to read
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@mcp.tool()
def encode_image_b64(path: str) -> tuple[str, str]:
    """Return (media_type, base64_str) for an image file path."""
    mime, _ = mimetypes.guess_type(path)
    media_type = mime or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return media_type, b64

@mcp.tool()
def save_image(path: str, img_bytes: str) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        img_bytes: Content to write to the file
    """
    try:
        dt = datetime.now()
        name = f"image_{dt.strftime("%Y_%m_%d")}{dt.hour}{dt.minute}{dt.second}.png"
        img = Image.open(BytesIO(img_bytes))
        img.save(os.path.join(path, name))
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
    
@mcp.tool()
def write_file(path: str, content: str) -> str:
    """Write content to a file.
    
    Args:
        path: Path to the file to write
        content: Content to write to the file
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

@mcp.tool()
def list_directory(path: str = ".") -> str:
    """List contents of a directory.
    
    Args:
        path: Path to the directory (defaults to current directory)
    """
    try:
        items = os.listdir(path)
        return json.dumps(items, indent=2)
    except Exception as e:
        return f"Error listing directory: {str(e)}"

@mcp.tool()
def create_directory(path: str) -> str:
    """Create a new directory.
    
    Args:
        path: Path to the directory to create
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"Successfully created directory: {path}"
    except Exception as e:
        return f"Error creating directory: {str(e)}"

@mcp.tool()
def delete_file(path: str) -> str:
    """Delete a file.
    
    Args:
        path: Path to the file to delete
    """
    try:
        os.remove(path)
        return f"Successfully deleted: {path}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@mcp.tool()
def get_weather_from_ip():
    """
    Gets the current, high, and low temperature in Fahrenheit for the user's
    location and returns it to the user.
    """
    # Get location coordinates from the IP address
    lat, lon = requests.get('https://ipinfo.io/json').json()['loc'].split(',')

    # Set parameters for the weather API call
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "auto"
    }

    # Get weather data
    weather_data = requests.get("https://api.open-meteo.com/v1/forecast", params=params).json()

    # Format and return the simplified string
    return (
        f"Current: {weather_data['current']['temperature_2m']}°F, "
        f"High: {weather_data['daily']['temperature_2m_max'][0]}°F, "
        f"Low: {weather_data['daily']['temperature_2m_min'][0]}°F"
    )

# Create a QR code
@mcp.tool()
def generate_qr_code(data: str, filename: str, image_path: str):
    """Generate a QR code image given data and an image path.

    Args:
        data: Text or URL to encode
        filename: Name for the output PNG file (without extension)
        image_path: Path to the image to be used in the QR code
    """
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(data)

    img = qr.make_image(image_factory=StyledPilImage, embedded_image_path=image_path)
    output_file = f"{filename}.png"
    img.save(output_file)

    return f"QR code saved as {output_file} containing: {data[:50]}..."

if __name__ == "__main__":
    mcp.run(transport='stdio')