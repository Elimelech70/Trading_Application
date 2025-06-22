import os
import sys


# Configuration
GOOGLE_DRIVE_SOURCE = '/content/drive/MyDrive/Business/Trade/software/Code'
COLAB_BASE_DIR = '/content/trading_system'
DIAGNOSIS_SOURCE = '/content/drive/Business/Trade/software/Code/Diagnosis'

#Mount Google Drive
"""Mount Google Drive in Colab"""
print("\n📁 Mounting Google Drive...")
try:
	from google.colab import drive
        drive.mount('/content/drive', force_remount=True)
        print("✅ Google Drive mounted successfully")
        return True
except ImportError:
        print("❌ Not running in Google Colab environment")
        return False
except Exception as e:
        print(f"❌ Error mounting Google Drive: {str(e)}")
        return False

