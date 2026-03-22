import os
import pickle
import re
import io
import mimetypes

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

import misc

# OAuth Scopes for Drive access
SCOPES = ['https://www.googleapis.com/auth/drive.file']


def authenticate_drive_with_client_info():
    creds = None
    if os.path.exists('token_drive.pickle'):
        with open('token_drive.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            client_config = {
                "installed": {
                    "client_id": "976112054211-225sp44rn82mq9nikkebdsbp6copaihq.apps.googleusercontent.com",
                    "client_secret": "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",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_drive.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('drive', 'v3', credentials=creds)
    return service


def upload_file():
    """
    Upload file lên Google Drive.

    Return format (BẮT BUỘC):
        "tenfile.xlsx|FILE_ID|mime_type"

    FILE_ID dùng cho mọi thao tác Google Drive (download / delete).
    """
    from PyQt6.QtWidgets import QFileDialog
    import os
    import mimetypes
    from googleapiclient.http import MediaFileUpload

    # 1️⃣ Chọn file
    file_path, _ = QFileDialog.getOpenFileName(
        None,
        "Chọn file để tải lên Google Drive"
    )

    if not file_path:
        print("❌ Không chọn file.")
        return None

    file_name = os.path.basename(file_path)

    # 2️⃣ Detect MIME type
    mime_type, _ = mimetypes.guess_type(file_path)
    mime_type = mime_type or 'application/octet-stream'

    print(f"📂 File MIME type: {mime_type}")

    # 3️⃣ Authenticate Google Drive
    service = authenticate_drive_with_client_info()

    # 4️⃣ Upload file
    file_metadata = {
        'name': file_name
    }

    media = MediaFileUpload(
        file_path,
        mimetype=mime_type,
        resumable=True
    )

    try:
        uploaded = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
    except Exception as e:
        print("❌ Lỗi upload Google Drive:", e)
        return None

    file_id = uploaded.get('id')

    if not file_id:
        print("❌ Upload thất bại: không nhận được fileId.")
        return None

    # 5️⃣ Chuẩn hoá chuỗi lưu DB / UI
    # ⚠️ TUYỆT ĐỐI KHÔNG ĐỔI FORMAT NÀY
    to_save = f"{file_name}|{file_id}|{mime_type}"

    print(f"✅ File '{file_name}' đã được tải lên Google Drive. ID: {file_id}")

    return to_save


def download_file(file_id, suggested_filename="downloaded_file"):
    if not file_id:
        print("❌ Không có file_id được cung cấp.")
        return

    service = authenticate_drive_with_client_info()

    # 🔍 Step 1: Get file metadata
    file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()
    original_name = file_info.get('name', suggested_filename)
    mime_type = file_info.get('mimeType', None)

    # 🔁 Step 2: Guess file extension
    ext = mimetypes.guess_extension(mime_type or '')
    ext = ext or ''  # fallback

    # 🔧 Step 3: Add extension if not present
    if not os.path.splitext(suggested_filename)[1] and ext:
        suggested_filename += ext

    # 🗂️ Step 4: Ask where to save
    save_path, _ = QFileDialog.getSaveFileName(
        None,
        "Chọn nơi lưu file",
        suggested_filename,
        "All Files (*.*)"
    )

    if not save_path:
        print("❌ Người dùng đã huỷ chọn nơi lưu.")
        return

    # 💾 Step 5: Download
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(save_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        status, done = downloader.next_chunk()
        if status:
            print(f"📥 Download progress: {int(status.progress() * 100)}%")

    print(f"✅ File đã được lưu tại: {save_path}")

def delete_file_from_drive(file_id):
    if not file_id:
        print("❌ Không có file_id được cung cấp.")
        return

    service = authenticate_drive_with_client_info()

    try:
        service.files().delete(fileId=file_id).execute()
        print(f"🗑️ File với ID {file_id} đã được xóa khỏi Google Drive.")
    except Exception as e:
        print(f"❌ Lỗi khi xóa file: {e}")


def remove_file_from_sale_lead(lead_id, file_id):
    result = misc.sql_one(
        "SELECT file FROM sale_lead WHERE lead_id = %s",
        (lead_id,)
    )

    if not result or not result[0]:
        return

    files = result[0].split('@@')
    files = [f for f in files if not f.endswith(f"|{file_id}")]

    new_value = '@@'.join(files) if files else None

    misc.sql_commit(
        "UPDATE sale_lead SET file = %s WHERE lead_id = %s",
        (new_value, lead_id)
    )
    print(f"✅ Đã cập nhật lại trường file cho lead_id = {lead_id}")

def update_file_list_in_ui(lead_id, uic):
    uic.txt_file.clear()
    result = misc.sql_one("SELECT file FROM sale_lead WHERE lead_id = %s", (lead_id,))
    if result and result[0]:
        ds_file = result[0].split('@@')
        for f in ds_file:
            try:
                name, fid, *_ = f.split('|')
                uic.txt_file.append(
                    f'<a href="{fid}">📎 {name}</a> &nbsp; ----------- &nbsp; '
                    f'<a href="delete:{fid}">🗑️ Xóa file</a><br>'
                )
            except Exception as e:
                print(f"Lỗi khi xử lý file: {f} – {e}")


def handle_upload(lead_id, uic):
    uic.txt_file.append('<span style="color:green;">⏳ Đang tải file lên Google Drive...</span>')
    uploaded = upload_file()  # format: tenfile|file_id|mime
    if not uploaded:
        return

    old_files = misc.sql_one("SELECT file FROM sale_lead WHERE lead_id = %s", (lead_id,))
    if old_files and old_files[0]:
        file_value = old_files[0] + '@@' + uploaded
    else:
        # ⚠️ Không prepend lead_id, phải giữ nguyên format file metadata
        file_value = uploaded

    misc.sql_commit("UPDATE sale_lead SET file = %s WHERE lead_id = %s", (file_value, lead_id))
    update_file_list_in_ui(lead_id, uic)

def handle_download_or_delete(url, lead_id, uic):
    """
    Hỗ trợ:
      - MỚI  : tenfile.xlsx|FILE_ID
      - CŨ   : FILE_ID
      - XÓA  : delete:FILE_ID

    Luôn đảm bảo download ra đúng tên file gốc.
    """
    raw = url.toString().strip()

    # ================= DELETE =================
    if raw.startswith("delete:"):
        file_id = raw.replace("delete:", "").strip()

        from PyQt6.QtWidgets import QMessageBox

        confirm = QMessageBox.question(
            uic.txt_file,
            "Xác nhận xóa",
            "Bạn có chắc muốn xóa file này khỏi Google Drive?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            delete_file_from_drive(file_id)
            remove_file_from_sale_lead(lead_id, file_id)
            refresh_file_list(lead_id, uic)
        return

    # ================= DOWNLOAD =================

    service = authenticate_drive_with_client_info()

    # ✅ FORMAT MỚI: name|id
    if "|" in raw:
        file_name, file_id = raw.split("|", 1)
        file_name = file_name.strip()
        file_id = file_id.strip()

    # ⚠️ FORMAT CŨ: chỉ có fileId → hỏi Google Drive lấy tên thật
    else:
        file_id = raw
        try:
            meta = service.files().get(
                fileId=file_id,
                fields="name"
            ).execute()
            file_name = meta.get("name", "downloaded_file")
            print(f"ℹ️ Lấy tên file từ Drive: {file_name}")
        except Exception as e:
            print("❌ Không lấy được tên file từ Drive:", e)
            file_name = "downloaded_file"

    print(f"📥 Download file: {file_name} | ID: {file_id}")
    download_file(file_id, suggested_filename=file_name)


def refresh_file_list(lead_id, uic):
    uic.txt_file.clear()

    result = misc.sql_one(
        "SELECT file FROM sale_lead WHERE lead_id = %s",
        (lead_id,)
    )

    if not result or not result[0]:
        return

    files = result[0].split('@@')

    for f in files:
        try:
            name, file_id, *_ = f.split('|')

            uic.txt_file.append(
                f'<a href="{name}|{file_id}">📎 {name}</a> &nbsp; '
                f'<a href="delete:{file_id}">🗑️ Xóa file</a><br>'
            )
        except Exception as e:
            print("❌ Lỗi parse file:", f, e)
