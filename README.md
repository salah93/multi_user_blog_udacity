# MultiUser Blog
[check it out](https://zippy-elf-142921.appspot.com/)

## How to deploy App!
### Setup environment
+ download proper python sdk
	+ Create a new Cloud Platform Console [project](https://console.cloud.google.com/project?_ga=1.141058290.1527192164.1476821067) or retrieve the project ID of an existing project from the Google Cloud Platform Console
		+ this guide saves this project ID into an environment variable APPID, save your id using an export statement:
		`export APPID="zippy-elf-835372"`
	+ download [google appengine sdk](https://cloud.google.com/appengine/docs/python/download), follow the installation instructions on the page

### Commands
```bash
git clone https://github.com/salah93/multi_user_blog_udacity.git
cd multi_user_blog_udacity
cat <<EOF >> temp.yml
application:
runtime: python27
api_version: 1
threadsafe: true

handlers:
- url: /.*
  script: run.app

libraries:
- name: jinja2
  version: latest
EOF
sed -e 's/application:.*$/application: '"$APPID"'/' temp.yml > app.yml
rm temp.yml
```

Assuming you inputted your [project id](#setup-environment) you can now view the app in the browser!@

#### local server
`/path/to/google_appengine/dev_appserver.py .`

#### deploying app
`/path/to/google_appengine/appcfg.py -V v1 update ./`
