set -e
inst(){ [ -d "$1-$2" ] || pip install -q --no-deps --break-system-packages --target "$1-$2" "$1==$2" 2>&1 | tail -1; }
for v in 2.2.5 2.3.3 3.0.3 3.1.1; do inst flask $v; done
for v in 2.2.3 2.3.8 3.0.6 3.1.3; do inst werkzeug $v; done
for v in 2.28.2 2.31.0 2.32.3; do inst requests $v; done
for v in 1.26.18 2.0.7 2.2.3 2.5.0; do inst urllib3 $v; done
[ -d shared ] || pip install -q --break-system-packages --target shared jinja2==3.1.4 markupsafe==2.1.5 itsdangerous==2.2.0 click==8.1.7 blinker==1.8.2 certifi idna charset-normalizer==3.3.2 2>&1 | tail -1
ls -d */ | tr '\n' ' '
