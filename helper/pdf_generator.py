import io

from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from helper.logger_utils import force_log


class PDFGenerator:
    """Utility class for generating PDF documents"""
    
    def __init__(self):
        self.logger_name = "PDFGenerator"
    
    def create_qr_pdf(self, qr_image: Image.Image, filename_prefix: str = "QR") -> io.BytesIO:
        """
        Create a PDF with the exact QR code image centered on the page
        
        Args:
            qr_image: PIL Image containing the QR code
            filename_prefix: Prefix for the filename (default: "QR")
            
        Returns:
            BytesIO buffer containing the PDF data
        """
        try:
            force_log(f"Creating PDF for QR image, size: {qr_image.size}", self.logger_name)
            
            # Create PDF buffer
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=letter)
            width, height = letter
            
            # Convert QR image to buffer for ReportLab
            qr_buffer = io.BytesIO()
            qr_image.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            # Calculate positioning to center the QR code
            qr_width, qr_height = qr_image.size
            
            # Scale to fit page nicely (max 80% of page width/height)
            max_width = width * 0.8
            max_height = height * 0.8
            scale_factor = min(max_width / qr_width, max_height / qr_height)
            
            scaled_width = qr_width * scale_factor
            scaled_height = qr_height * scale_factor
            
            # Center on page
            x_pos = (width - scaled_width) / 2
            y_pos = (height - scaled_height) / 2
            
            force_log(f"PDF layout: page={width}x{height}, QR scaled to {scaled_width}x{scaled_height} at ({x_pos}, {y_pos})", self.logger_name)
            
            # Draw the exact QR image
            c.drawImage(ImageReader(qr_buffer), x_pos, y_pos, scaled_width, scaled_height)
            
            # Save and finalize PDF
            c.save()
            pdf_buffer.seek(0)
            
            force_log(f"PDF created successfully, size: {len(pdf_buffer.getvalue())} bytes", self.logger_name)
            return pdf_buffer
            
        except Exception as e:
            force_log(f"Error creating PDF: {e}", self.logger_name, "ERROR")
            raise e
    
    def create_wifi_qr_pdf(self, qr_image: Image.Image, wifi_name: str) -> io.BytesIO:
        """
        Create a PDF specifically for Wifi QR codes
        
        Args:
            qr_image: PIL Image containing the Wifi QR code
            wifi_name: Wifi network name for filename
            
        Returns:
            BytesIO buffer containing the PDF data
        """
        try:
            force_log(f"Creating Wifi QR PDF for network: {wifi_name}", self.logger_name)
            return self.create_qr_pdf(qr_image, f"Wifi-QR-{wifi_name}")
            
        except Exception as e:
            force_log(f"Error creating Wifi QR PDF: {e}", self.logger_name, "ERROR")
            raise e
    
    def get_pdf_filename(self, wifi_name: str) -> str:
        """
        Generate a clean filename for the Wifi QR PDF
        
        Args:
            wifi_name: Wifi network name
            
        Returns:
            Clean filename string
        """
        # Replace spaces and special characters
        clean_name = wifi_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
        # Remove any other problematic characters
        clean_name = ''.join(c for c in clean_name if c.isalnum() or c in '-_.')
        return f"Wifi-QR-{clean_name}.pdf"