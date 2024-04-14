from flask import Flask, render_template, request, redirect, url_for, flash
from flask_pymongo import PyMongo
import os
import hashlib
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect
from config import Config
from flask import jsonify

app = Flask(__name__)
app.config.from_object(Config)
mongo = PyMongo(app)
csrf = CSRFProtect(app)

class UploadForm(FlaskForm):
    file = FileField('파일 선택', validators=[DataRequired()])
    submit = SubmitField('제출')

@app.route('/complete')
def complete():
    return render_template('complete.html')

@app.route('/error')
def error():
    return render_template('error.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            file.seek(0, os.SEEK_END)  # 파일 크기를 확인하기 위해 끝으로 이동
            file_size = file.tell()  # 파일 크기 가져오기
            file.seek(0)  # 다시 파일의 시작으로 이동

            if file_size > 20971520:  # 20MB 초과 시
                # 파일 업로드 실패: BAD REQUEST 라고 출력된다.
                # 용량 제한은 1차로 클라이언트 javascript에서 거르고, 2차로 서버에서 거른다.
                # 서버에 20MB보다 큰 자료가 업로드됐다면 명백한 정책 위반이다.
                return jsonify({'flash': '파일 크기는 20MB를 초과할 수 없습니다. - server'}), 200
            else:
                handle_file_upload(file)
                # return jsonify({'redirect': url_for('complete')})
                return redirect(url_for('complete'))
            
    return render_template('index.html', form=form)




def insert_file_record(filename, filepath, hashes):
    try:
        mongo.db.uploads.insert_one(
            {
                "filename": filename,
                "filenames": [filename],
                "filepath": filepath,
                'md5': hashes['md5'],
                'sha1': hashes['sha1'],
                'sha256': hashes['sha256'],
                'sha512': hashes['sha512'],
            },
        )
        
    except Exception as e:
        print(f'ERROR: Database insert - {str(e)}')

def update_file_record(sha1, filename):
    try:
        mongo.db.uploads.update_one(
            {"sha1": sha1},
            {
                "$addToSet": {"filenames": filename},
            }
        )
    except Exception as e:
        print(f'ERROR: Database update - {str(e)}')

def save_file(file, file_relative_path):
    
    if not os.path.exists(file_relative_path):
        file.seek(0)
        file.save(file_relative_path)
        print(f'file saved...')


def generate_sha1_hash(file_content):
    return hashlib.sha1(file_content).hexdigest()


def generate_file_hashes_set(file_content):
    return {
        'sha1': hashlib.sha1(file_content).hexdigest(),
        'md5': hashlib.md5(file_content).hexdigest(),
        'sha256': hashlib.sha256(file_content).hexdigest(),
        'sha512': hashlib.sha512(file_content).hexdigest()
    }

def generate_file_hashes_set_without_sha1(file_content, sha1):
    return {
        'sha1': sha1,
        'md5': hashlib.md5(file_content).hexdigest(),
        'sha256': hashlib.sha256(file_content).hexdigest(),
        'sha512': hashlib.sha512(file_content).hexdigest()
    }

def handle_file_upload(file):
    file_content = file.read()
    sha1_hash = generate_sha1_hash(file_content)
    today = datetime.now()
    date_path = os.path.join(app.config['UPLOAD_FOLDER'], today.strftime('%Y'), today.strftime('%m'), today.strftime('%d'))
    file_relative_path = os.path.join(date_path, sha1_hash)  # Use SHA1 hash as filename
    os.makedirs(date_path, exist_ok=True)
    
    # 파일 저장
    save_file(file, file_relative_path)

    # DB 저장
    if mongo.db.uploads.find_one({"sha1": sha1_hash}) is None:
        hashes = generate_file_hashes_set_without_sha1(file_content, sha1_hash)
        insert_file_record(file.filename, file_relative_path, hashes)
    else:
        update_file_record(sha1_hash, file.filename)

if __name__ == '__main__':
    app.run(debug=True)
