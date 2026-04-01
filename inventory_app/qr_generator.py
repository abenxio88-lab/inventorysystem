"""
QR Code Generation Module
==========================
Generate QR codes and barcodes for products.
Uses qrcode library (pure Python with Pillow).
"""

import os
import io
import base64
import logging
from typing import Optional, Tuple

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

# Try to import qrcode library
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logging.warning("qrcode library not available - QR generation disabled")


def generate_qr_code(
    data: str,
    size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
    logo_path: Optional[str] = None,
    logo_size: Tuple[int, int] = None
) -> Image.Image:
    """
    Generate a QR code image.
    
    Args:
        data: Data to encode in QR code
        size: Box size (pixels per module)
        border: Border width in modules
        fill_color: QR code color
        back_color: Background color
        logo_path: Optional logo to embed in center
        logo_size: Size of logo (width, height)
    
    Returns:
        PIL Image object
    """
    if not QR_AVAILABLE:
        raise ImportError("qrcode library required. Install with: pip install qrcode[pil]")
    
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img = img.convert('RGB')
    
    # Add logo if provided
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            
            # Calculate logo size (default 20% of QR code)
            qr_size = img.size[0]
            if logo_size is None:
                logo_size = (int(qr_size * 0.2), int(qr_size * 0.2))
            
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            
            # Ensure logo has alpha channel
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            # Calculate position (center)
            position = (
                (qr_size - logo_size[0]) // 2,
                (qr_size - logo_size[1]) // 2
            )
            
            # Paste logo with transparency
            img.paste(logo, position, logo)
            
        except Exception as e:
            logging.error(f"Failed to add logo: {e}")
    
    return img


def generate_product_qr(product: dict, include_fields: list = None) -> str:
    """
    Generate QR code for a product.
    
    Args:
        product: Product dictionary
        include_fields: Specific fields to include (default: all)
    
    Returns:
        Base64 encoded PNG image
    """
    # Build QR data
    if include_fields:
        qr_data = {k: v for k, v in product.items() if k in include_fields}
    else:
        qr_data = {
            'id': product.get('id'),
            'sku': product.get('sku'),
            'model': product.get('model'),
            'stock': product.get('stock'),
            'price': product.get('selling_price')
        }
    
    # Convert to JSON string
    import json
    data_str = json.dumps(qr_data)
    
    # Generate QR code
    img = generate_qr_code(data_str)
    
    # Convert to base64 for storage
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def save_product_qr(
    product: dict,
    output_path: str,
    size: int = 10,
    with_label: bool = True
) -> str:
    """
    Save product QR code to file.
    
    Args:
        product: Product dictionary
        output_path: Path to save QR code image
        size: QR code size
        with_label: Add product name label below QR
    
    Returns:
        Path to saved file
    """
    # Generate QR
    qr_img = generate_qr_code(
        data=f"PRODUCT:{product.get('id')}:{product.get('sku', '')}",
        size=size
    )
    
    if with_label:
        # Create image with label
        label_height = 40
        total_height = qr_img.size[1] + label_height
        
        # Create new image with white background
        labeled_img = Image.new('RGB', (qr_img.size[0], total_height), 'white')
        labeled_img.paste(qr_img, (0, 0))
        
        # Draw label
        draw = ImageDraw.Draw(labeled_img)
        
        # Try to use a nice font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        # Center text
        text = f"{product.get('model', 'Unknown')}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (qr_img.size[0] - text_width) // 2
        text_y = qr_img.size[1] + 10
        
        draw.text((text_x, text_y), text, fill='black', font=font)
        
        qr_img = labeled_img
    
    # Save
    qr_img.save(output_path, 'PNG')
    return output_path


def generate_barcode_text(product: dict) -> str:
    """
    Generate barcode-compatible text (EAN-13 format).
    
    Note: For actual barcode images, you'd need additional libraries.
    This generates the text that can be used with barcode fonts.
    """
    # Create a numeric code from product ID
    product_id = str(product.get('id', 0)).zfill(12)
    
    # Calculate EAN-13 check digit
    digits = [int(d) for d in product_id]
    odd_sum = sum(digits[::2])
    even_sum = sum(digits[1::2])
    total = odd_sum + (even_sum * 3)
    check_digit = (10 - (total % 10)) % 10
    
    return product_id + str(check_digit)


def print_qr_labels(
    products: list,
    output_path: str,
    labels_per_page: int = 12,
    page_size: str = "A4"
) -> str:
    """
    Create printable QR code labels sheet.
    
    Args:
        products: List of products to label
        output_path: Path to save PDF
        labels_per_page: Number of labels per page
        page_size: Page size (A4, Letter)
    
    Returns:
        Path to saved PDF
    """
    # For PDF generation, we'd need reportlab
    # This is a stub showing the interface
    
    try:
        from reportlab.lib.pagesizes import A4, letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.utils import ImageReader
        REPORTLAB_AVAILABLE = True
    except ImportError:
        REPORTLAB_AVAILABLE = False
        logging.warning("reportlab not available - PDF generation disabled")
        return ""
    
    if not REPORTLAB_AVAILABLE:
        raise ImportError("reportlab required for PDF generation")
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=A4)
    page_width, page_height = A4
    
    # Calculate grid
    cols = 3
    rows = labels_per_page // cols
    label_width = page_width / cols
    label_height = page_height / rows
    
    # Generate labels
    for i, product in enumerate(products[:labels_per_page]):
        col = i % cols
        row = i // cols
        
        x = col * label_width
        y = page_height - (row + 1) * label_height
        
        # Generate QR
        qr_img = generate_qr_code(
            data=f"PRODUCT:{product.get('id')}:{product.get('sku', '')}",
            size=8
        )
        
        # Convert for reportlab
        img_buffer = io.BytesIO()
        qr_img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        # Draw QR code
        qr_size = min(label_width, label_height) * 0.7
        qr_x = x + (label_width - qr_size) / 2
        qr_y = y + (label_height - qr_size) / 2 + 20
        
        c.drawImage(ImageReader(img_buffer), qr_x, qr_y, qr_size, qr_size)
        
        # Draw product info
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(
            x + label_width / 2,
            y + 15,
            product.get('model', 'Unknown')[:20]
        )
        
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            x + label_width / 2,
            y + 5,
            f"SKU: {product.get('sku', 'N/A')}"
        )
    
    c.save()
    return output_path


def scan_qr_from_file(image_path: str) -> Optional[dict]:
    """
    Scan QR code from image file.
    
    Note: Requires pyzbar library for decoding.
    
    Returns:
        Decoded data as dictionary, or None if failed
    """
    try:
        from pyzbar.pyzbar import decode
        from PIL import Image
    except ImportError:
        logging.warning("pyzbar not available - QR scanning disabled")
        return None
    
    try:
        # Open image
        img = Image.open(image_path)
        
        # Decode QR codes
        decoded = decode(img)
        
        if decoded:
            # Return first decoded QR code
            data = decoded[0].data.decode('utf-8')
            
            # Try to parse as product data
            if data.startswith('PRODUCT:'):
                parts = data.split(':')
                return {
                    'type': 'product',
                    'id': int(parts[1]) if len(parts) > 1 else None,
                    'sku': parts[2] if len(parts) > 2 else None
                }
            
            # Try to parse as JSON
            try:
                import json
                return json.loads(data)
            except:
                return {'raw_data': data}
        
        return None
        
    except Exception as e:
        logging.error(f"QR scan failed: {e}")
        return None


def generate_qr_for_all_products(inventory: list) -> int:
    """
    Generate QR codes for all products in inventory.
    Saves to data/qr_codes/ directory.
    
    Returns:
        Number of QR codes generated
    """
    qr_dir = os.path.join(get_data_dir(), "qr_codes")
    os.makedirs(qr_dir, exist_ok=True)
    
    count = 0
    for product in inventory:
        try:
            filename = f"qr_{product.get('id', product.get('model', 'unknown'))}.png"
            output_path = os.path.join(qr_dir, filename)
            
            save_product_qr(product, output_path)
            count += 1
            
        except Exception as e:
            logging.error(f"Failed to generate QR for {product.get('model')}: {e}")
    
    return count


# Convenience functions
def create_qr(data: str, output_path: str) -> str:
    """Quick QR code generation and save."""
    img = generate_qr_code(data)
    img.save(output_path, 'PNG')
    return output_path


def qr_to_base64(data: str) -> str:
    """Generate QR code and return as base64 string."""
    img = generate_qr_code(data)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return base64.b64encode(buffer.read()).decode('utf-8')
