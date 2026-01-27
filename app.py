from flask import Flask, render_template, abort
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


# --------------------
# RUN
# --------------------

if __name__ == "__main__":
    app.run(debug=True)
