import os
from flask import Flask, render_template, session, request, redirect, url_for, flash
from flask_mysqldb import MySQL
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = '!@#$%'

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'portofolio'
app.config['UPLOAD_FOLDER'] = 'static/img'

mysql = MySQL(app)

@app.route('/')
def home():
    current_user_id = session.get('user_id')
    cur = mysql.connection.cursor()
    profile = None
    OWNER_ID = 1 
    cur.execute("SELECT name, bio, photo FROM users WHERE id = %s", (OWNER_ID,))
    data = cur.fetchone()
    if data:
        profile = {
            'name': data[0],
            'bio': data[1],
            'photo': data[2]
        }
    cur.execute("SELECT id, name, level, icon FROM skills")
    skills_data = cur.fetchall()
    cur.execute("SELECT id, title, description, image, link FROM projects")
    projects_data = cur.fetchall()
    cur.close()
    return render_template('home.html', profile=profile, skills=skills_data, projects=projects_data, user_id=current_user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'is_logged_in' in session:
        return redirect(url_for('home'))
    if request.method == 'POST':
        username = request.form['inpUsername']
        passwd = request.form['inpPass']
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, username FROM users WHERE username = %s AND password = %s", (username, passwd))
        result = cur.fetchone()
        if result:
            session['user_id'] = result[0] 
            session['username'] = result[1]
            return redirect(url_for('home'))
        else:
            flash('Login Failed. Check your username and password.', 'danger')
            return render_template('login.html')
    else:
        return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('home'))

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/edit_profile/<int:user_id>', methods=['GET'])
def edit_profile(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        flash('Akses ditolak atau ID Pengguna salah.', 'danger')
        return redirect(url_for('home'))
    cur = mysql.connection.cursor()
    profile_data = None
    cur.execute("SELECT name, bio, photo FROM users WHERE id = %s", (user_id,))
    data = cur.fetchone()
    cur.close()
    if data:
        profile_data = {
             'name': data[0], 
             'bio': data[1], 
             'photo': data[2]
           }
    return render_template('edit_profile.html', profile=profile_data, user_id=user_id)

@app.route('/add_skill_page', methods=['GET'])
def add_skill_page():
    if not session.get('user_id'):
        return redirect(url_for('login')) 
    return render_template('add_skill.html')
    
@app.route('/add_project_page', methods=['GET'])
def add_project_page():
    if not session.get('user_id'):
        return redirect(url_for('login')) 
    return render_template('add_project.html')

@app.route('/edit_skill_page/<int:skill_id>', methods=['GET'])
def edit_skill_page(skill_id):
    if 'user_id' not in session:
        flash('Akses ditolak. Anda harus login.', 'danger')
        return redirect(url_for('login'))
    skill_data = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, name, level, icon FROM skills WHERE id = %s", (skill_id,))
        result = cur.fetchone()
        cur.close()
        if result:
            skill_data = {'id': result[0], 'name': result[1], 'level': result[2], 'icon': result[3]}
        else:
            flash(f'Skill dengan ID {skill_id} tidak ditemukan.', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        flash('Terjadi kesalahan server saat mengambil data.', 'danger')
        return redirect(url_for('home'))
    return render_template('edit_skill.html', skill=skill_data)

@app.route('/edit_project_page/<int:project_id>', methods=['GET'])
def edit_project_page(project_id):
    if 'user_id' not in session:
        flash('Akses ditolak. Anda harus login.', 'danger')
        return redirect(url_for('login'))
    project_data = None
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT id, title, description, image, link FROM projects WHERE id = %s", (project_id,))
        result = cur.fetchone()
        cur.close()
        if result:
            project_data = {'id': result[0], 'title': result[1], 'description': result[2], 'image': result[3], 'link': result[4]}
        else:
            flash(f'Project dengan ID {project_id} tidak ditemukan.', 'danger')
            return redirect(url_for('home'))
    except Exception as e:
        flash('Terjadi kesalahan server saat mengambil data.', 'danger')
        return redirect(url_for('home'))
    return render_template('edit_project.html', project=project_data)

@app.route('/api/add_skill', methods=['POST'])
def add_skill():
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        name = request.form.get('name')
        level = request.form.get('level')
        icon = request.form.get('icon')
        if not name or not level:
            flash("Nama dan Level Skill diperlukan.", 'danger')
            return redirect(url_for('add_skill_page'))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO skills (name, level, icon) VALUES (%s, %s, %s)", 
                    (name, level, icon))
        mysql.connection.commit()
        cur.close()
        flash(f"Skill '{name}' berhasil ditambahkan!", 'success')
        return redirect(url_for('home') + '#skill')
    except Exception as e:
        print(f"Error saat menambah skill: {e}")
        flash("Terjadi kesalahan server saat menambah skill.", 'danger')
        return redirect(url_for('add_skill_page'))

@app.route('/api/update_skill_form/<int:skill_id>', methods=['POST'])
def update_skill_form(skill_id):
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        name = request.form.get('name')
        level = request.form.get('level')
        icon = request.form.get('icon')
        if not name or not level:
            flash("Nama dan Level diperlukan.", 'danger')
            return redirect(url_for('edit_skill_page', skill_id=skill_id))
        cur = mysql.connection.cursor()
        cur.execute("UPDATE skills SET name = %s, level = %s, icon = %s WHERE id = %s", (name, level, icon, skill_id))
        mysql.connection.commit()
        cur.close()
        if cur.rowcount == 0:
            flash("Gagal: Skill tidak ditemukan atau tidak ada perubahan.", 'danger')
        else:
            flash(f"Skill '{name}' berhasil diperbarui.", 'success')
        return redirect(url_for('home') + '#skill')
    except Exception as e:
        print(f"Error saat update skill: {e}")
        flash("Terjadi kesalahan server saat update skill.", 'danger')
        return redirect(url_for('edit_skill_page', skill_id=skill_id))

@app.route('/api/delete_skill_form/<int:skill_id>', methods=['POST'])
def delete_skill_form(skill_id):
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM skills WHERE id = %s", (skill_id,))
        mysql.connection.commit()
        cur.close()
        if cur.rowcount == 0:
            flash("Gagal: Skill tidak ditemukan.", 'danger')
        else:
            flash("Skill berhasil dihapus.", 'success')
        return redirect(url_for('home') + '#skill')
    except Exception as e:
        print(f"Error saat delete skill: {e}")
        flash("Terjadi kesalahan server saat menghapus skill.", 'danger')
        return redirect(url_for('home') + '#skill')

@app.route('/api/add_project', methods=['POST'])
def add_project():
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')
        link = request.form.get('link')
        if not title or not description:
            flash("Judul dan Deskripsi Project diperlukan.", 'danger')
            return redirect(url_for('add_project_page'))
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO projects (title, description, image, link) VALUES (%s, %s, %s, %s)", 
                    (title, description, image, link))
        mysql.connection.commit()
        cur.close()
        flash(f"Project '{title}' berhasil ditambahkan!", 'success')
        return redirect(url_for('home') + '#project')
    except Exception as e:
        print(f"Error saat menambah project: {e}")
        flash("Terjadi kesalahan server saat menambah project.", 'danger')
        return redirect(url_for('add_project_page'))

@app.route('/api/update_project_form/<int:project_id>', methods=['POST'])
def update_project_form(project_id):
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        title = request.form.get('title')
        description = request.form.get('description')
        image = request.form.get('image')
        link = request.form.get('link')
        if not title or not description:
            flash("Judul dan Deskripsi Project diperlukan.", 'danger')
            return redirect(url_for('edit_project_page', project_id=project_id))
        cur = mysql.connection.cursor()
        query = "UPDATE projects SET title = %s, description = %s, image = %s, link = %s WHERE id = %s"
        cur.execute(query, (title, description, image, link, project_id))
        mysql.connection.commit()
        cur.close()
        if cur.rowcount == 0:
            flash("Gagal: Project tidak ditemukan atau tidak ada perubahan.", 'danger')
        else:
            flash(f"Project '{title}' berhasil diperbarui.", 'success')
        return redirect(url_for('home') + '#project')
    except Exception as e:
        print(f"Error saat update project: {e}")
        flash("Terjadi kesalahan server saat update project.", 'danger')
        return redirect(url_for('edit_project_page', project_id=project_id))

@app.route('/api/delete_project_form/<int:project_id>', methods=['POST'])
def delete_project_form(project_id):
    if 'user_id' not in session:
        flash("Akses ditolak. Anda harus login.", 'danger')
        return redirect(url_for('login'))
    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM projects WHERE id = %s", (project_id,))
        mysql.connection.commit()
        cur.close()
        if cur.rowcount == 0:
            flash("Gagal: Project tidak ditemukan.", 'danger')
        else:
            flash("Project berhasil dihapus.", 'success')
        return redirect(url_for('home') + '#project')
    except Exception as e:
        print(f"Error saat delete project: {e}")
        flash("Terjadi kesalahan server saat menghapus project.", 'danger')
        return redirect(url_for('home') + '#project')

@app.route('/api/update_profile_text/<int:user_id>', methods=['POST'])
def update_profile_text(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        flash('Akses ditolak atau ID Pengguna salah.', 'danger')
        return redirect(url_for('home'))
    try:
        name = request.form.get('name')
        bio = request.form.get('bio')
        if not name and not bio:
            flash("Harap berikan Nama atau Bio untuk diperbarui.", 'danger')
            return redirect(url_for('edit_profile', user_id=user_id))
        update_fields = []
        update_values = []
        if name:
            update_fields.append("name = %s") 
            update_values.append(name)
        if bio:
            update_fields.append("bio = %s")
            update_values.append(bio)
        set_clause = ", ".join(update_fields)
        update_values.append(user_id)
        cur = mysql.connection.cursor()
        cur.execute(f"UPDATE users SET {set_clause} WHERE id = %s", tuple(update_values))
        mysql.connection.commit()
        cur.close()
        if cur.rowcount == 0:
            flash("Pengguna tidak ditemukan atau tidak ada perubahan.", 'danger')
        else:
            flash("Nama dan Bio berhasil diperbarui!", 'success')
        return redirect(url_for('home'))
    except Exception as e:
        print(f"Error saat memperbarui data teks: {e}")
        flash("Terjadi kesalahan server saat memperbarui teks.", 'danger')
        return redirect(url_for('edit_profile', user_id=user_id))

@app.route('/api/update_profile_photo/<int:user_id>', methods=['POST'])
def update_profile_photo(user_id):
    if 'user_id' not in session or session['user_id'] != user_id:
        flash('Akses ditolak atau ID Pengguna salah.', 'danger')
        return redirect(url_for('home'))
    if 'photo' not in request.files:
        flash("Bagian file 'photo' tidak ditemukan.", 'danger')
        return redirect(url_for('edit_profile', user_id=user_id))
    file = request.files['photo']
    if file.filename == '':
        flash("Tidak ada file yang dipilih.", 'danger')
        return redirect(url_for('edit_profile', user_id=user_id))
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        photo_filename = f"user_{user_id}_{original_filename}"
        upload_dir = app.config.get('UPLOAD_FOLDER', 'static/img')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        try:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], photo_filename)
            file.save(file_path)
        except Exception as e:
            print(f"Error saat menyimpan file: {e}")
            flash("Gagal menyimpan file di server.", 'danger')
            return redirect(url_for('edit_profile', user_id=user_id))
        try:
            cur = mysql.connection.cursor()
            cur.execute("UPDATE users SET photo = %s WHERE id = %s", (photo_filename, user_id))
            mysql.connection.commit()
            cur.close()
            flash("Foto profil berhasil diperbarui!", 'success')
            return redirect(url_for('home'))
        except Exception as e:
            print(f"Database error saat update foto: {e}")
            flash("Gagal menyimpan nama file di database.", 'danger')
            return redirect(url_for('edit_profile', user_id=user_id))
    else:
        flash("Format file tidak diizinkan.", 'danger')
        return redirect(url_for('edit_profile', user_id=user_id))

if __name__ == '__main__':
    app.run(debug=True)