import uuid
import hashlib

class FileService:

    @staticmethod
    def generate_secure_filename(filename: str):
        ext = filename.split(".")[-1]
        return f"{uuid.uuid4().hex}.{ext}"

    @staticmethod
    def calculate_hash(path: str):
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha.update(chunk)
        return sha.hexdigest()


# app/shared/utils/file_service.py
# import clamd  # python-clamd for ClamAV integration
# from python_magic import magic  # MIME type detection

# class FileService:
#     ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
#     MAX_FILE_SIZE = 10 * 1024 * 1024
    
#     @staticmethod
#     def validate_file(file: UploadFile) -> tuple[bool, str]:
#         # Check extension
#         ext = Path(file.filename).suffix.lower()
#         if ext not in FileService.ALLOWED_EXTENSIONS:
#             return False, f"Extension {ext} not allowed"
        
#         # Check MIME type
#         file.file.seek(0)
#         mime = magic.from_buffer(file.file.read(1024), mime=True)
#         file.file.seek(0)
#         if mime not in {"application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"}:
#             return False, f"MIME type {mime} not allowed"
        
#         return True, ""
    
#     @staticmethod
#     def scan_for_malware(file_path: str) -> bool:
#         """Returns True if file is clean"""
#         try:
#             cd = clamd.ClamdUnixSocket()
#             result = cd.scan(file_path)
#             return result["stream"][0] == "OK"
#         except Exception as e:
#             logger.warning(f"Antivirus scan failed: {e}")
#             # Fail open or closed based on policy
#             return os.getenv("ANTIVIRUS_FAIL_OPEN", "true").lower() == "true"