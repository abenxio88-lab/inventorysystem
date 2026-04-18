"""
Advanced Barcode System
========================
Complete barcode generation and scanning system.
Supports QR codes, Code128, EAN13, and camera-based scanning.
"""

import os
import io
import base64
import logging
from typing import Optional, Tuple, List

try:
    from .utils import get_data_dir
except (ImportError, ModuleNotFoundError):
    from utils import get_data_dir

# Try to import required libraries
try:
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False
    logging.warning("qrcode library not available")

try:
    import barcode
    from barcode.writer import ImageWriter
    BARCODE_AVAILABLE = True
except ImportError:
    BARCODE_AVAILABLE = False
    logging.warning("python-barcode library not available - install with: pip install python-barcode")

try:
    import cv2
    import numpy as np
    from pyzbar.pyzbar import decode
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV/pyzbar not available - camera scanning disabled")


# ============================================================================
# QR CODE GENERATION
# ============================================================================

def generate_qr_code(
    data: str,
    size: int = 10,
    border: int = 4,
    fill_color: str = "black",
    back_color: str = "white",
    logo_path: Optional[str] = None
) -> Image.Image:
    """
    Generate a QR code image.
    
    Args:
        data: Data to encode
        size: Box size in pixels
        border: Border width
        fill_color: QR code color
        back_color: Background color
        logo_path: Optional logo to embed
    
    Returns:
        PIL Image object
    """
    if not QR_AVAILABLE:
        raise ImportError("qrcode library required")
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    img = img.convert('RGB')
    
    # Add logo if provided
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path)
            logo_size = (int(img.size[0] * 0.2), int(img.size[1] * 0.2))
            logo = logo.resize(logo_size, Image.Resampling.LANCZOS)
            
            if logo.mode != 'RGBA':
                logo = logo.convert('RGBA')
            
            position = (
                (img.size[0] - logo_size[0]) // 2,
                (img.size[1] - logo_size[1]) // 2
            )
            
            img.paste(logo, position, logo)
        except Exception as e:
            logging.error(f"Failed to add logo: {e}")
    
    return img


def generate_product_qr(product: dict) -> str:
    """Generate QR code for a product and return as base64."""
    import json
    
    qr_data = {
        'id': product.get('id'),
        'sku': product.get('sku'),
        'model': product.get('model'),
        'stock': product.get('stock'),
        'price': product.get('selling_price')
    }
    
    data_str = json.dumps(qr_data)
    img = generate_qr_code(data_str)
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


def save_product_qr(product: dict, output_path: str, with_label: bool = True) -> str:
    """Save product QR code to file with optional label."""
    qr_img = generate_qr_code(
        data=f"PRODUCT:{product.get('id')}:{product.get('sku', '')}"
    )
    
    if with_label:
        label_height = 40
        total_height = qr_img.size[1] + label_height
        
        labeled_img = Image.new('RGB', (qr_img.size[0], total_height), 'white')
        labeled_img.paste(qr_img, (0, 0))
        
        draw = ImageDraw.Draw(labeled_img)

        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except (OSError, IOError):
            font = ImageFont.load_default()
        
        text = f"{product.get('model', 'Unknown')}"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (qr_img.size[0] - text_width) // 2
        text_y = qr_img.size[1] + 10
        
        draw.text((text_x, text_y), text, fill='black', font=font)
        qr_img = labeled_img
    
    qr_img.save(output_path, 'PNG')
    return output_path


# ============================================================================
# BARCODE GENERATION (Code128, EAN13)
# ============================================================================

def generate_barcode_code128(
    code: str,
    output_path: str,
    width: int = 3,
    height: int = 50,
    font_size: int = 10,
    text: str = ""
) -> str:
    """
    Generate Code128 barcode.
    
    Args:
        code: Barcode value
        output_path: Path to save image
        width: Bar width
        height: Barcode height
        font_size: Text font size
        text: Custom text below barcode
    
    Returns:
        Path to saved file
    """
    if not BARCODE_AVAILABLE:
        raise ImportError("python-barcode library required. Install with: pip install python-barcode")
    
    try:
        # Create barcode
        code128 = barcode.get('code128', code, writer=ImageWriter())
        
        # Save with options
        options = {
            'module_width': width,
            'module_height': height,
            'font_size': font_size,
            'text': text or code,
            'write_text': True,
        }
        
        code128.save(output_path, options=options)
        return output_path + '.png'
        
    except Exception as e:
        logging.error(f"Failed to generate Code128 barcode: {e}")
        raise


def generate_barcode_ean13(
    code: str,
    output_path: str,
    width: int = 3,
    height: int = 50
) -> str:
    """
    Generate EAN13 barcode.
    
    Args:
        code: 12 or 13 digit code
        output_path: Path to save
        width: Bar width
        height: Barcode height
    
    Returns:
        Path to saved file
    """
    if not BARCODE_AVAILABLE:
        raise ImportError("python-barcode library required")
    
    try:
        # Ensure 13 digits
        if len(code) == 12:
            code = code + '0'  # Will be calculated
        elif len(code) > 13:
            code = code[:13]
        
        ean13 = barcode.get('ean13', code, writer=ImageWriter())
        
        options = {
            'module_width': width,
            'module_height': height,
            'write_text': True,
        }
        
        ean13.save(output_path, options=options)
        return output_path + '.png'
        
    except Exception as e:
        logging.error(f"Failed to generate EAN13 barcode: {e}")
        raise


def generate_product_barcode(product: dict, barcode_type: str = 'code128') -> str:
    """Generate barcode for a product."""
    # Generate barcode text
    if barcode_type == 'code128':
        barcode_text = f"PROD{product.get('id', 0):06d}"
    elif barcode_type == 'ean13':
        # Create 12-digit code from product ID
        barcode_text = f"{product.get('id', 0):012d}"
    else:
        barcode_text = str(product.get('sku', product.get('id', '')))
    
    # Save to QR codes directory
    qr_dir = os.path.join(get_data_dir(), "barcodes")
    os.makedirs(qr_dir, exist_ok=True)
    
    output_path = os.path.join(qr_dir, f"barcode_{product.get('id', 0)}")
    
    if barcode_type == 'code128':
        return generate_barcode_code128(barcode_text, output_path)
    elif barcode_type == 'ean13':
        return generate_barcode_ean13(barcode_text, output_path)
    else:
        # Default to QR code
        output_path += '.png'
        save_product_qr(product, output_path)
        return output_path


# ============================================================================
# BARCODE/QR SCANNING (Camera-based)
# ============================================================================

def scan_barcode_from_image(image_path: str) -> Optional[dict]:
    """
    Scan barcode or QR code from image file.
    
    Returns:
        Decoded data or None if failed
    """
    if not OPENCV_AVAILABLE:
        logging.warning("OpenCV/pyzbar not available for scanning")
        return None
    
    try:
        # Read image
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Decode barcodes and QR codes
        decoded = decode(img)
        
        if decoded:
            # Return first decoded result
            data = decoded[0].data.decode('utf-8')
            barcode_type = decoded[0].type
            
            # Try to parse as product data
            if data.startswith('PRODUCT:'):
                parts = data.split(':')
                return {
                    'type': 'product',
                    'id': int(parts[1]) if len(parts) > 1 else None,
                    'sku': parts[2] if len(parts) > 2 else None,
                    'barcode_type': barcode_type
                }
            
            return {
                'raw_data': data,
                'barcode_type': barcode_type
            }
        
        return None
        
    except Exception as e:
        logging.error(f"Scan failed: {e}")
        return None


def scan_barcode_from_camera() -> Optional[dict]:
    """
    Open camera and scan barcode/QR code in real-time.
    
    Returns:
        Decoded data or None if cancelled
    """
    if not OPENCV_AVAILABLE:
        raise ImportError("OpenCV and pyzbar required for camera scanning")
    
    try:
        # Open camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            raise ValueError("Could not open camera")
        
        scanned_data = None
        timeout = 300  # 5 seconds at 60 FPS
        
        while timeout > 0:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # Decode barcodes
            decoded = decode(frame)
            
            # Draw rectangles around detected codes
            for obj in decoded:
                # Draw bounding box
                points = obj.polygon
                if len(points) == 4:
                    pts = [(p.x, p.y) for p in points]
                    cv2.polylines(frame, [np.array(pts, np.int32)], True, (0, 255, 0), 2)
                
                # Get data
                data = obj.data.decode('utf-8')
                barcode_type = obj.type
                
                # Display data
                cv2.putText(frame, f"{barcode_type}: {data}", (10, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # Store first result
                if scanned_data is None:
                    scanned_data = {
                        'raw_data': data,
                        'barcode_type': barcode_type
                    }
            
            # Show frame
            cv2.imshow('Barcode Scanner - Press Q to quit', frame)
            
            # Check for quit or scan
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            
            if scanned_data:
                timeout -= 1
                if timeout <= 0:
                    break
        
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        
        return scanned_data
        
    except Exception as e:
        logging.error(f"Camera scan failed: {e}")
        try:
            cap.release()
            cv2.destroyAllWindows()
        except (NameError, Exception):
            # NameError if cap not defined, Exception for cleanup failures
            pass
        return None


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

def generate_barcodes_for_inventory(inventory: list, barcode_type: str = 'code128') -> int:
    """Generate barcodes for all products in inventory."""
    qr_dir = os.path.join(get_data_dir(), "barcodes")
    os.makedirs(qr_dir, exist_ok=True)
    
    count = 0
    for product in inventory:
        try:
            generate_product_barcode(product, barcode_type)
            count += 1
        except Exception as e:
            logging.error(f"Failed to generate barcode for {product.get('model')}: {e}")
    
    return count


def generate_qr_codes_for_inventory(inventory: list) -> int:
    """Generate QR codes for all products."""
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


# ============================================================================
# PRINT LABELS
# ============================================================================

def print_barcode_labels(
    products: list,
    output_path: str,
    labels_per_page: int = 12,
    barcode_type: str = 'code128'
) -> str:
    """
    Create printable barcode/QR label sheets.
    
    Args:
        products: List of products to label
        output_path: Path to save PDF
        labels_per_page: Labels per page
        barcode_type: Type of barcode to generate
    
    Returns:
        Path to saved PDF
    """
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
        
        # Generate barcode/QR
        if barcode_type in ['code128', 'ean13']:
            barcode_path = generate_product_barcode(product, barcode_type)
            c.drawImage(barcode_path, x + 10, y + 40, width=200, height=60)
        else:
            # Use QR code
            qr_img = generate_qr_code(
                data=f"PRODUCT:{product.get('id')}:{product.get('sku', '')}",
                size=8
            )
            
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            qr_size = min(label_width, label_height) * 0.6
            qr_x = x + (label_width - qr_size) / 2
            qr_y = y + (label_height - qr_size) / 2 + 20
            
            c.drawImage(ImageReader(img_buffer), qr_x, qr_y, qr_size, qr_size)
        
        # Draw product info
        c.setFont("Helvetica-Bold", 10)
        c.drawCentredString(
            x + label_width / 2,
            y + 15,
            product.get('model', 'Unknown')[:25]
        )
        
        c.setFont("Helvetica", 8)
        c.drawCentredString(
            x + label_width / 2,
            y + 5,
            f"Rs. {product.get('selling_price', 0):,.2f}"
        )
    
    c.save()
    return output_path


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_barcode_type(code: str) -> str:
    """Detect barcode type from code format."""
    if len(code) == 12 or len(code) == 13:
        return 'ean13'
    elif code.isdigit():
        return 'code128'
    else:
        return 'qr'  # Default to QR for alphanumeric


def validate_barcode(code: str, barcode_type: str) -> bool:
    """Validate barcode format."""
    if barcode_type == 'ean13':
        if len(code) != 13:
            return False
        # Validate EAN13 check digit
        try:
            digits = [int(d) for d in code]
            odd_sum = sum(digits[::2])
            even_sum = sum(digits[1::2])
            total = odd_sum + (even_sum * 3)
            return total % 10 == 0
        except (ValueError, TypeError):
            return False
    elif barcode_type == 'code128':
        return len(code) > 0
    else:
        return True  # QR codes can be any length


def check_scanner_availability() -> dict:
    """Check which scanning features are available."""
    return {
        'qr_generation': QR_AVAILABLE,
        'barcode_generation': BARCODE_AVAILABLE,
        'camera_scanning': OPENCV_AVAILABLE,
        'file_scanning': OPENCV_AVAILABLE,
        'pdf_labels': 'reportlab' in [m for m in dir() if not m.startswith('_')]
    }
