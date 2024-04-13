from flask import Flask, render_template, request, redirect, url_for, flash
import os
import hashlib
from datetime import datetime
import csv
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'very_secret_key'
app.config['UPLOAD_FOLDER'] = 'uploads/'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
csrf = CSRFProtect(app)

class UploadForm(FlaskForm):
    introduction = StringField('자기소개', validators=[DataRequired()])
    file = FileField('파일 선택', validators=[DataRequired()])
    submit = SubmitField('제출')

@app.route('/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        introduction = form.introduction.data
        file = form.file.data
        filename = file.filename
        md5_hash = hashlib.md5(file.read()).hexdigest()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], md5_hash)
        log_file_path = f"{app.config['UPLOAD_FOLDER']}/{md5_hash}.csv"

        if not os.path.exists(file_path):
            file.seek(0)
            file.save(file_path)

        with open(log_file_path, 'a', encoding='utf-8-sig', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if os.stat(log_file_path).st_size == 0:
                writer.writerow(['타임스탬프', '파일명'])
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([timestamp, filename])

        flash('제출이 완료되었습니다.')
        return redirect(url_for('submission_complete'))
    return render_template('upload_form.html', form=form)

@app.route('/submission_complete')
def submission_complete():
    return render_template('submission_complete.html')

if __name__ == '__main__':
    app.run(debug=True)
