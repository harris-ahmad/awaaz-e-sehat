# awaaz-e-sehat-v1

To run the Django app on your localhost, run the following command in the same root directory wherein
`manage.py` file is hosted.

```bash
python manage.py runserver
```

To run the test suite of the entire system, run the following command

```bash
python manage.py runserver
```

Currently, there are a total of 8 tests written, so this is the following output that you should expect:

```bash
Found 8 test(s).
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
........
----------------------------------------------------------------------
Ran 8 tests in 0.704s

OK
Destroying test database for alias 'default'...
```

For a specific app's test suite, use the following command

```bash
python manage.py test app_name
```