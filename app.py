from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import json

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

job_list = []
resume_list = []

def add_justified_text(pdf, text, x, y, max_width):
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        if pdf.stringWidth(test_line, "Helvetica", 12) < max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    for line in lines:
        pdf.drawString(x, y, line)
        y -= 15

    return y

@app.route("/")
def index():
    return render_template('index.html', jobs=job_list)

@app.route('/job_list')
def job_list_page():
    return render_template('jobs.html', jobs=job_list)

@app.route('/add_job_page')
def add_job_page():
    return render_template('add_job.html')

@app.route('/add_job', methods=['POST'])
def add_job():
    title = request.form['title']
    company = request.form['company']
    date = request.form['date']
    status = request.form['status']
    notes = request.form.get('notes', '')

    job = {"title": title, "company": company, "date": date, "status": status, "notes": notes}
    job_list.append(job)
    flash("Job added successfully!", "success")
    return redirect(url_for('job_list_page'))

@app.route('/edit_job/<int:job_index>', methods=['GET', 'POST'])
def edit_job(job_index):
    if 0 <= job_index < len(job_list):
        job = job_list[job_index]

        if request.method == 'POST':
            job['title'] = request.form['title']
            job['company'] = request.form['company']
            job['date'] = request.form['date']
            job['status'] = request.form['status']
            job['notes'] = request.form.get('notes', '')

            flash("Job updated successfully!", "success")
            return redirect(url_for('job_list_page'))

        return render_template('edit_job.html', job=job, job_index=job_index)

    return "Job not found!", 404

@app.route('/delete_job/<int:job_index>', methods=['GET', 'POST'])
def delete_job(job_index):
    if 0 <= job_index < len(job_list):
        del job_list[job_index]
        flash("Job deleted successfully!", "success")
        return redirect(url_for('job_list_page'))

    return "Job not found!", 404

@app.route('/create_resume')
def create_resume():
    return render_template('create_resume.html')

@app.route('/save_resume', methods=['POST'])
def save_resume():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    linkedin = request.form.get('linkedin', '')
    github = request.form.get('github', '')
    summary = request.form.get('summary', 'No summary provided')
    skills = request.form['skills'].split(',')
    certifications = request.form['certifications'].split(',')

    def parse_json(field_name):
        field_data = request.form.get(field_name, '[]')
        try:
            return json.loads(field_data)
        except json.JSONDecodeError:
            return []

    experience = parse_json('experience')
    education = parse_json('education')
    projects = parse_json('projects')

    resume = {
        "name": name,
        "email": email,
        "phone": phone,
        "linkedin": linkedin,
        "github": github,
        "summary": summary,
        "skills": skills,
        "experience": experience,
        "education": education,
        "projects": projects,
        "certifications": certifications
    }

    resume_list.append(resume)
    flash("Resume saved successfully!", "success")
    return redirect(url_for('saved_resumes'))

@app.route('/saved_resumes')
def saved_resumes():
    return render_template('saved_resumes.html', resumes=resume_list, enumerate=enumerate)

def check_page_overflow(pdf, y_position):
    if y_position < 50:
        pdf.showPage()
        pdf.setFont("Helvetica", 12)
        return 750
    return y_position

@app.route('/download_resume/<int:resume_index>')
def download_resume(resume_index):
    if 0 <= resume_index < len(resume_list):
        resume = resume_list[resume_index]
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle(f"Resume_{resume['name']}.pdf")

        y_position = 750  
        pdf.setFont("Helvetica-Bold", 16)
        name_text = resume['name']
        text_width = pdf.stringWidth(name_text, "Helvetica-Bold", 16)
        x_position = (letter[0] - text_width) / 2 
        pdf.drawString(x_position, y_position, name_text)
        y_position -= 30

        pdf.setFont("Helvetica", 12)
        contact_info = f"{resume['phone']} | {resume['email']} | {resume.get('linkedin', 'N/A')} | {resume.get('github', 'N/A')}"
        y_position = add_justified_text(pdf, contact_info, 50, y_position, max_width=500)
        pdf.line(50, y_position, 550, y_position)
        y_position -= 20  

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Summary:")
        y_position -= 20
        pdf.setFont("Helvetica", 12)
        y_position = add_justified_text(pdf, resume['summary'], 60, y_position, max_width=500)
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Education:")
        y_position -= 20

        if resume.get("education"):
            for edu in resume['education']:
                degree = edu.get('degree', 'Unknown Degree')
                institute = edu.get('institute', 'Unknown Institution')
                year = edu.get('year', 'Unknown Year')
                marks = edu.get('marks', 'Not Available')

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(60, y_position, f"{degree}")
                y_position -= 15
                pdf.setFont("Helvetica", 12)
                pdf.drawString(60, y_position, f"{institute} ({year})")
                y_position -= 15
                pdf.drawString(60, y_position, f"Marks: {marks}")
                y_position -= 20
                y_position = check_page_overflow(pdf, y_position)

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Skills:")
        y_position -= 20

        for skill in resume['skills']:
            pdf.drawString(60, y_position, f"• {skill.strip()}")
            y_position -= 20
        y_position -= 20

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Work Experience:")
        y_position -= 20

        if resume.get("experience"):  # Check if experience exists
            for exp in resume['experience']:
                job_role = exp.get('job_role', 'Unknown Role')  # Fix key name
                duration = exp.get('year', 'Unknown Duration')  # Ensure correct key
                description = exp.get('description', 'No details provided.')

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(60, y_position, f"{job_role} - ({duration})")  # Role & Year
                y_position -= 15
                pdf.setFont("Helvetica", 12)
                y_position = add_justified_text(pdf, description, 60, y_position, max_width=500)
                y_position -= 15
                # Check if a new page is needed
                y_position = check_page_overflow(pdf, y_position)
        else:
            pdf.drawString(60, y_position, "No work experience added.")
            y_position -= 20
        y_position -= 20

        # Projects Section
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Projects:")
        y_position -= 20

        if resume.get("projects"):
            for project in resume['projects']:
                name = project.get('name', 'Untitled Project')
                description = project.get('description', 'No description provided.')

                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(60, y_position, name)
                y_position -= 15
                pdf.setFont("Helvetica", 12)
                y_position = add_justified_text(pdf, description, 60, y_position, max_width=500)
                y_position -= 15
                # Check if a new page is needed
                y_position = check_page_overflow(pdf, y_position)

        else:
            pdf.drawString(60, y_position, "No projects added.")
            y_position -= 20
        y_position -= 20
       

        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(50, y_position, "Certifications:")
        y_position -= 20

        for certification in resume['certifications']:
            pdf.drawString(60, y_position, f"• {certification.strip()}")
            y_position -= 20
        y_position -= 20

        pdf.showPage()
        pdf.save()

        buffer.seek(0)
        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="{resume["name"].replace(" ", "_")}_Resume.pdf"'

        return response

    return "Invalid resume index!", 404

if __name__ == '__main__':
    app.run(debug=True)
