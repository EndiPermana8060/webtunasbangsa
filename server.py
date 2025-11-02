from flask import Flask, render_template, jsonify, request
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import threading
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# ==============================
# KONFIGURASI
# ==============================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "endipermana68@gmail.com"
SENDER_PASSWORD = "zodolslpeakjpsgk"
RECEIVER_EMAIL = "kazehaku315@gmail.com"

# Folder untuk menyimpan file upload sementara
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Maksimal 16MB

# Konfigurasi Google Sheets
GSHEET_CREDENTIALS = 'serene-smoke-465304-s6-efe217d26f96.json'  # Ganti dengan path file JSON Anda
GSHEET_NAME = 'Data Calon Mahasiswa Baru'  # Nama Google Sheet Anda
WORKSHEET_NAME = 'Sheet1'  # Nama worksheet/tab

# ==============================
# FUNGSI GOOGLE SHEETS
# ==============================
def simpan_ke_gsheet(data):
    """Simpan data pendaftaran ke Google Sheets"""
    try:
        # Setup credentials
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GSHEET_CREDENTIALS, scope)
        client = gspread.authorize(creds)
        
        # Buka spreadsheet
        sheet = client.open(GSHEET_NAME).worksheet(WORKSHEET_NAME)
        
        # Siapkan data untuk diinput
        row_data = [
            data.get('nama_lengkap', ''),
            data.get('tempat_lahir', ''),
            data.get('tanggal_lahir', ''),
            data.get('alamat', ''),
            data.get('no_hp', ''),
            data.get('email', ''),
            data.get('nama_ortu', '-'),  # Default '-' jika tidak ada
            data.get('no_hp_ortu', '-'),  # Default '-' jika tidak ada
            datetime.now().strftime('%d/%m/%Y %H:%M:%S')  # Timestamp
        ]
        
        # Tambahkan baris baru
        sheet.append_row(row_data)
        
        print(f"✅ Data berhasil disimpan ke Google Sheets untuk {data.get('nama_lengkap')}")
        return True
        
    except Exception as e:
        print(f"❌ Error menyimpan ke Google Sheets: {e}")
        return False

# ==============================
# FUNGSI EMAIL
# ==============================
def kirim_email_async(nama, email_pendaftar, data, file_paths):
    """Fungsi kirim email di background"""
    try:
        subject = f"Pendaftaran Baru: {nama}"
        
        # Body HTML yang menarik
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f4f4f4;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 30px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #2c5f2d 0%, #4a9d4e 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .header p {{
                    margin: 10px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 30px 40px;
                }}
                .greeting {{
                    font-size: 16px;
                    color: #333;
                    margin-bottom: 20px;
                }}
                .info-box {{
                    background-color: #f8f9fa;
                    border-left: 4px solid #2c5f2d;
                    border-radius: 5px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .info-row {{
                    display: flex;
                    padding: 10px 0;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .info-row:last-child {{
                    border-bottom: none;
                }}
                .info-label {{
                    font-weight: 600;
                    color: #2c5f2d;
                    min-width: 160px;
                    font-size: 14px;
                }}
                .info-value {{
                    color: #333;
                    font-size: 14px;
                }}
                .attachments {{
                    background-color: #fff8e1;
                    border: 1px solid #ffd54f;
                    border-radius: 5px;
                    padding: 15px 20px;
                    margin-top: 25px;
                }}
                .attachments h3 {{
                    margin: 0 0 10px 0;
                    font-size: 15px;
                    color: #f57c00;
                }}
                .attachments ul {{
                    margin: 0;
                    padding-left: 20px;
                }}
                .attachments li {{
                    color: #666;
                    font-size: 13px;
                    margin: 5px 0;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    border-top: 1px solid #e0e0e0;
                }}
                .footer p {{
                    margin: 5px 0;
                    font-size: 13px;
                    color: #666;
                }}
                .timestamp {{
                    background-color: #e8f5e9;
                    color: #2c5f2d;
                    padding: 10px;
                    border-radius: 5px;
                    text-align: center;
                    font-size: 13px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎓 Pendaftaran Calon Mahasiswa Baru</h1>
                    <p>Yayasan Sinar Tunas Bakti Bangsa</p>
                </div>
                
                <div class="content">
                    <p class="greeting">Halo Tim Yayasan 👋,</p>
                    <p class="greeting">Ada pendaftar baru melalui form website. Berikut detail lengkapnya:</p>
                    
                    <div class="info-box">
                        <div class="info-row">
                            <div class="info-label">Nama Lengkap</div>
                            <div class="info-value">{data.get('nama_lengkap')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Tempat Lahir</div>
                            <div class="info-value">{data.get('tempat_lahir')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Tanggal Lahir</div>
                            <div class="info-value">{data.get('tanggal_lahir')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Alamat</div>
                            <div class="info-value">{data.get('alamat')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">No. HP</div>
                            <div class="info-value">{data.get('no_hp')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Email</div>
                            <div class="info-value">{data.get('email')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">Nama Orang Tua/Wali</div>
                            <div class="info-value">{data.get('nama_ortu', '-')}</div>
                        </div>
                        <div class="info-row">
                            <div class="info-label">No HP Orang Tua/Wali</div>
                            <div class="info-value">{data.get('no_hp_ortu', '-')}</div>
                        </div>
                    </div>
                    
                    <div class="attachments">
                        <h3>📎 Dokumen Terlampir:</h3>
                        <ul>
                            <li>KTP Pendaftar</li>
                            <li>Kartu Keluarga (KK)</li>
                            <li>Transkrip Nilai / Ijazah</li>
                        </ul>
                    </div>
                    
                    <div class="timestamp">
                        ⏰ Dikirim pada: {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}
                    </div>
                </div>
                
                <div class="footer">
                    <p><strong>Yayasan Sinar Tunas Bakti Bangsa</strong></p>
                    <p>Jl. Jingga Raya D1 No.12, Jakarta Utara</p>
                    <p>Email: sinartunasbaktibangsa@gmail.com | Telp: (021) 450 7140</p>
                </div>
            </div>
        </body>
        </html>
        """

        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = subject
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, "html"))

        # Lampiran
        for path in file_paths:
            if os.path.exists(path):
                with open(path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={os.path.basename(path)}"
                    )
                    msg.attach(part)

        # Kirim email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        print(f"✅ Email berhasil dikirim untuk {nama} ({email_pendaftar})")

    except Exception as e:
        print(f"❌ Error saat kirim email ke {email_pendaftar}: {e}")

    finally:
        # Bersihkan file sementara
        for path in file_paths:
            if os.path.exists(path):
                try:
                    os.remove(path)
                    print(f"🗑️ File {path} berhasil dihapus")
                except:
                    pass
# ==============================
# ROUTES
# ==============================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/daftar', methods=['POST'])
def daftar():
    try:
        # Ambil data form
        data = {
            'nama_lengkap': request.form.get('nama_lengkap'),
            'tempat_lahir': request.form.get('tempat_lahir'),
            'tanggal_lahir': request.form.get('tanggal_lahir'),
            'alamat': request.form.get('alamat'),
            'no_hp': request.form.get('no_hp'),
            'email': request.form.get('email'),
            'nama_ortu': request.form.get('nama_ortu', '-'),  # Optional
            'no_hp_ortu': request.form.get('no_hp_ortu', '-')  # Optional
        }

        # Upload files
        file_paths = []
        for field in ['ktp', 'kk', 'transkrip']:
            if field in request.files:
                file = request.files[field]
                if file and file.filename:
                    # Buat nama file yang aman
                    filename = f"{data['nama_lengkap'].replace(' ', '_')}_{field}_{file.filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    file_paths.append(filepath)
                    print(f"📁 File {filename} berhasil disimpan")

        # Simpan ke Google Sheets (SYNC - langsung)
        gsheet_success = simpan_ke_gsheet(data)

        # Kirim email (ASYNC - background)
        thread = threading.Thread(
            target=kirim_email_async,
            args=(data['nama_lengkap'], data['email'], data, file_paths)
        )
        thread.daemon = True  # Thread akan otomatis berhenti saat program utama berhenti
        thread.start()

        return jsonify({
            "status": "success",
            "message": "Data berhasil dikirim",
            "gsheet_saved": gsheet_success
        }), 200

    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == '__main__':
    print("🚀 Server Flask dimulai...")
    print(f"📁 Upload folder: {UPLOAD_FOLDER}")
    app.run(debug=True)