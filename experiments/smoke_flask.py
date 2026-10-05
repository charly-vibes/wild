from flask import Flask, jsonify, url_for, redirect, request, make_response, abort, session
app = Flask(__name__); app.secret_key = "k"
@app.route("/")
def idx(): return jsonify(ok=True, q=request.args.get("q"))
@app.route("/go")
def go(): return redirect(url_for("idx", q="x"))
@app.route("/c")
def c():
    r = make_response("hi"); r.set_cookie("a", "b"); session["s"] = 1; return r
@app.route("/e")
def e(): abort(404)
@app.errorhandler(404)
def nf(_): return "nf", 404
cl = app.test_client()
assert cl.get("/?q=1").json == {"ok": True, "q": "1"}
assert cl.get("/go").status_code == 302
assert cl.get("/c").status_code == 200
assert cl.get("/e").status_code == 404
print("OK")
