from flask import Flask, render_template, abort, request, redirect
import os
import markdown
import frontmatter

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")


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

@app.route("/contact")
def contact():
    return render_template("contact.html")

SERVICES_DIR = "pages/services"

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

        # PAGE BODY
        content=html_content,

        # META
        title=post.get("title"),
        description=post.get("description"),

        # HERO
        hero_title=post.get("hero_title"),
        hero_subtitle=post.get("hero_subtitle"),

        # GLOBAL
        phone=post.get("phone"),

        # SIDEBAR LISTS
        service_areas=post.get("service_areas"),
        mobile_services=post.get("mobile_services"),

        # CTA
        cta_heading=post.get("cta_heading"),
        cta_subtext=post.get("cta_subtext")
    )



@app.route("/blog")
def blog():
    return render_template("blog.html")


@app.route("/blog/how-to-keep-home-clean")
def blog_post():
    return render_template("blog_post.html")


CONTENT_ROOT = "pages"

@app.route("/admin/content")
def admin_content():
    files = []

    for root, dirs, filenames in os.walk(CONTENT_ROOT):
        for name in filenames:
            if name.endswith(".md"):
                full = os.path.join(root, name)
                files.append(full.replace("\\","/"))

    return render_template(
        "admin_content_list.html",
        files=files
    )


@app.route("/admin/content/edit/<path:file_path>", methods=["GET","POST"])
def admin_edit_content(file_path):

    # Allow both:
    # services/file.md
    # pages/services/file.md
    if file_path.startswith("pages/"):
        file_path = file_path.replace("pages/", "", 1)

    real_path = os.path.join(CONTENT_ROOT, file_path)

    if not os.path.exists(real_path):
        abort(404)

    if request.method == "POST":
        new_content = request.form["content"]

        # Normalize Windows newlines -> Unix
        new_content = new_content.replace("\r\n", "\n")

        # Prevent exponential blank lines
        while "\n\n\n" in new_content:
            new_content = new_content.replace("\n\n\n", "\n\n")

        # Remove leading junk only
        new_content = new_content.lstrip()

        with open(real_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(new_content)

        return redirect("/admin/content")

    with open(real_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template(
        "admin_edit_content.html",
        path=file_path,
        content=content
    )

if __name__ == "__main__":
    app.run(debug=True)
