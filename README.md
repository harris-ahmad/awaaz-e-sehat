# awaaz-e-sehat

To run the app, configure the following environment variables in your local terminal environment:

```bash
FLASK_ENV=deployment
FLASK_APP=app.py
```

Next, make sure that you have all dependencies set up and installed to the matching versions given in the requirements.txt file. Download
the PyPI packages using the following command:

```bash
pip install -r requirements.txt
```

You're all set to run the Awaaz-e-Sehat's first native build. To run, type the following command in your root directory:

```bash
flask run
```

To run it on a custom IP address, type in the following command: 

```bash
flask run --host a.b.c.d
```

**Note:** `a.b.c.d` is any 32-bit IP address.

To test the app on your mobile device (iOS or Android), type in the following URL in your browser window:

```text
http://a.b.c.d:5000/
```
This will direct you to awaaz-e-sehat's homepage (`index.html`). 

In order to run the app on SSL-protected protocol (`https`), type in the following command to run the app:
```bash
flask run --cert=adhoc
```
and similarly for mobile:
```bash
flask run --cert=adhoc --host a.b.c.d
```
