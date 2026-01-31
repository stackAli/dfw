from flask import Flask, render_template, abort, request, redirect
import os
import markdown
import frontmatter
import smtplib
from email.message import EmailMessage
from functools import wraps
from flask import session, flash
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)
app.secret_key = "13cbff75cd4b36dd9b5cdb166ff5ab4be9d3c99ff569442173d926341b67c3b2"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = "scrypt:32768:8:1$pve5IekZUQfdT8JL$b810de9d5cc55a84dc5219fc468e1c3322efec4bc6bf6bd58bd5567237019899ed0ebe7865fcacc224d223e6c6ddd785220dd9c307b8067474ac4bb831f9ee59"


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "images", "blog")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect("/admin/login")
        return f(*args, **kwargs)
    return decorated_function



# --------------------
# BASIC ROUTES
# --------------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/services")
def services():
    return render_template("services.html")

@app.route("/locations")
def locations():
    return render_template("locations.html")

@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        service = request.form.get("service")
        message = request.form.get("message")

        msg = EmailMessage()
        msg["Subject"] = "New Website Lead - DFW Clean Collective"
        msg["From"] = "DFW Clean Collective <aftabdawood36@gmail.com>"
        msg["To"] = "aftabdawood@gmail.com"
        msg["Reply-To"] = email

        msg.set_content(f"""
New Contact Form Submission

Name: {name}
Email: {email}
Phone: {phone}
Service Requested: {service}

Message:
{message}
""")

        try:
            server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
            server.login("aftabdawood36@gmail.com", "afix fnuf qkps pkfs")
            server.send_message(msg)
            server.quit()
            print("EMAIL SENT")

            return render_template("contact.html", success=True)

        except Exception as e:
            print("EMAIL ERROR:", e)
            return "Email failed: " + str(e)

    return render_template("contact.html")

SERVICES_DIR = os.path.join(BASE_DIR, "pages", "services")

@app.route("/services/<slug>")
def service_page(slug):

    md_path = os.path.join(PAGES_DIR, f"{slug}.md")

    if not os.path.exists(md_path):
        abort(404)

    post = frontmatter.load(md_path)
    data = post.metadata

    return render_template(
        "baseservice.html",
        phone="9809902722",
        phone_display="(980) 990-2722",
        **data
    )
# --------------------
# DYNAMIC MD PAGES
# --------------------

@app.route("/<slug>")
def md_page(slug):
    md_path = os.path.join(PAGES_DIR, f"{slug}.md")

    if not os.path.exists(md_path):
        abort(404)

    # Parse front-matter + markdown
    post = frontmatter.load(md_path)

    html_content = markdown.markdown(
        post.content,
        extensions=["fenced_code", "tables"]
    )

    return render_template(
    "baselocation.html",
    content=html_content,
    title=post.get("title"),
    description=post.get("description"),
    hero_title=post.get("hero_title"),
    hero_subtitle=post.get("hero_subtitle"),
    phone=post.get("phone"),

    service_areas=post.get("service_areas"),
    mobile_services=post.get("mobile_services"),

    location_services=post.get("mobile_services", []),
    current_location=slug,

    cta_heading=post.get("cta_heading"),
    cta_subtext=post.get("cta_subtext")
)


@app.route("/blog")
def blog():
    posts = load_blog_posts()
    return render_template("blog.html", posts=posts)



@app.route("/blog/<slug>")
def blog_post(slug):

    md_path = os.path.join(BLOG_DIR, f"{slug}.md")

    if not os.path.exists(md_path):
        abort(404)

    post = frontmatter.load(md_path)

    html_content = markdown.markdown(
        post.content,
        extensions=["fenced_code","tables"]
    )

    return render_template(
        "blog_post.html",
        content=html_content,
        title=post.get("title"),
        hero_title=post.get("hero_title"),
        hero_subtitle=post.get("hero_subtitle")
    )



CONTENT_ROOT = os.path.join(BASE_DIR, "pages")


@app.route("/admin/login", methods=["GET","POST"])
def admin_login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):


            session["admin_logged_in"] = True
            return redirect("/admin/content")
        else:
            return render_template("admin_login.html", error="Invalid credentials")

    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect("/admin/login")

@app.route("/admin/content")
@admin_required
def admin_content():

    categories = {
        "services": [],
        "locations": [],
        "service_locations": [],
        "blogs": []
    }

    for root, dirs, filenames in os.walk(CONTENT_ROOT):
        for name in filenames:

            if not name.endswith(".md"):
                continue

            full = os.path.join(root, name)
            rel = os.path.relpath(full, CONTENT_ROOT)
            rel = rel.replace("\\", "/")

            filename = name.lower()

            # BLOGS
            if rel.startswith("blog/"):
                categories["blogs"].append(rel)

            # SERVICE × LOCATION
            elif "-service-" in filename:
                categories["service_locations"].append(rel)

            # LOCATION PAGES
            elif filename.endswith("-cleaning-services.md"):
                categories["locations"].append(rel)

            # BASE SERVICES
            else:
                categories["services"].append(rel)

    return render_template(
        "admin_content_list.html",
        categories=categories
    )

@app.route("/admin/content/edit/<path:file_path>", methods=["GET","POST"])
@admin_required
def admin_edit_content(file_path):

    file_path = file_path.lstrip("/")

    if file_path.startswith("pages/"):
        file_path = file_path.replace("pages/", "", 1)

    real_path = os.path.normpath(
        os.path.join(CONTENT_ROOT, file_path)
    )

    if not real_path.startswith(CONTENT_ROOT):
        abort(403)

    if not os.path.exists(real_path):
        abort(404)

    # ============================
    # READ EXISTING CONTENT
    # ============================

    with open(real_path, "r", encoding="utf-8") as f:
        old_content = f.read()

    old_slug_match = re.search(r"slug:\s*([a-zA-Z0-9\-]+)", old_content)
    old_slug = old_slug_match.group(1) if old_slug_match else None

    if request.method == "POST":

        new_content = request.form["content"]

        new_content = new_content.replace("\r\n", "\n")
        new_content = new_content.lstrip()

        new_slug_match = re.search(r"slug:\s*([a-zA-Z0-9\-]+)", new_content)

        if not new_slug_match:
            return "ERROR: slug field missing", 400

        new_slug = new_slug_match.group(1)

        new_path = real_path

        # ============================
        # RENAME FILE IF SLUG CHANGED
        # ============================

        if old_slug and new_slug != old_slug:
            new_path = os.path.join(
                os.path.dirname(real_path),
                f"{new_slug}.md"
            )

            os.rename(real_path, new_path)

        # ============================
        # SAVE UPDATED CONTENT
        # ============================

        with open(new_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)

        return redirect("/admin/content")

    return render_template(
        "admin_edit_content.html",
        path=file_path,
        content=old_content
    )

@app.route("/admin/content/delete/<path:file_path>", methods=["POST"])
@admin_required
def admin_delete_content(file_path):

    file_path = file_path.lstrip("/")

    if file_path.startswith("pages/"):
        file_path = file_path.replace("pages/", "", 1)

    real_path = os.path.normpath(
        os.path.join(CONTENT_ROOT, file_path)
    )

    if not real_path.startswith(CONTENT_ROOT):
        abort(403)

    if not os.path.exists(real_path):
        abort(404)

    os.remove(real_path)

    return redirect("/admin/content")

import re

@app.route("/admin/content/new", methods=["GET","POST"])
@admin_required
def admin_new_content():

    if request.method == "POST":

        content = request.form["content"]
        image = request.files.get("image")

        # =========================
        # EXTRACT SLUG FROM FRONTMATTER
        # =========================

        match = re.search(r"slug:\s*([a-zA-Z0-9\-]+)", content)

        if not match:
            return "ERROR: slug field is required in frontmatter", 400

        slug = match.group(1)

        # Blog files always go here
        real_path = os.path.join(CONTENT_ROOT, "blog", f"{slug}.md")

        image_path = ""

        # =========================
        # HANDLE IMAGE UPLOAD
        # =========================

        if image and image.filename:
            filename = image.filename.lower().replace(" ", "-")
            save_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(save_path)

            image_path = f"/static/images/blog/{filename}"

            # Inject image into frontmatter
            content = content.replace(
                "image:",
                f"image: {image_path}"
            )

            # Replace body placeholder
            content = content.replace(
                "/static/images/blog/UPLOAD-IMAGE-WILL-AUTO-APPEAR.webp",
                image_path,
                1
            )

        # =========================
        # ENSURE BLOG FOLDER EXISTS
        # =========================

        os.makedirs(os.path.dirname(real_path), exist_ok=True)

        # =========================
        # SAVE FILE
        # =========================

        with open(real_path, "w", encoding="utf-8") as f:
            f.write(content.strip())

        return redirect("/admin/content")

    return render_template("admin_new_content.html")

SERVICES_DIR = "pages"

def load_services():
    services = []

    for filename in os.listdir(SERVICES_DIR):
        if filename.endswith(".md"):
            path = os.path.join(SERVICES_DIR, filename)
            post = frontmatter.load(path)

            slug = post.get("slug") or filename.replace(".md", "")
            title = post.get("title") or slug.replace("-", " ").title()

            services.append({
                "title": title,
                "slug": slug
            })

    services.sort(key=lambda x: x["title"])
    return services


BLOG_DIR = os.path.join(PAGES_DIR, "blog")

def load_blog_posts():
    posts = []

    if not os.path.exists(BLOG_DIR):
        return posts

    for filename in os.listdir(BLOG_DIR):
        if filename.endswith(".md"):
            path = os.path.join(BLOG_DIR, filename)
            post = frontmatter.load(path)

            posts.append({
                "title": post.get("title"),
                "slug": post.get("slug") or filename.replace(".md",""),
                "excerpt": post.get("excerpt"),
                "tag": post.get("tag"),
                "read_time": post.get("read_time"),
                "image": post.get("image")   # ⭐ NEW
            })

    return posts


@app.context_processor
def inject_globals():
    return {
        "services_list": load_services()
    }
# =========================
# BOOKING ROUTES
# =========================

@app.route("/booking")
def booking():
    return render_template("booking.html")


@app.route("/login")
def login():
    return render_template("login.html")



import secrets
print(secrets.token_hex(32))
if __name__ == "__main__":
    app.run(debug=True)
