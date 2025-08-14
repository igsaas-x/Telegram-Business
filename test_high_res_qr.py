#!/usr/bin/env python3
"""
Test high resolution QR generator
"""

from helper.qr_generator import QRGenerator

def test_high_res_qr():
    """Test high resolution QR code generation"""
    print("Testing high resolution QR code generation...")
    
    try:
        qr_gen = QRGenerator()
        img = qr_gen.generate_wifi_qr_with_text("iCoffee", "123455")
        
        print(f"✓ High-res QR generated, size: {img.size}")
        
        # Save test image
        img.save("high_res_qr_test.png")
        print("✓ Saved as 'high_res_qr_test.png'")
        
        # Test conversion to bytes
        bio = qr_gen.image_to_bytes(img)
        print(f"✓ Image size in bytes: {len(bio.getvalue())}")
        
        print("\n🎉 High resolution QR test passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_high_res_qr()