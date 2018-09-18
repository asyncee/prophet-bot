bootstrap:
	rm -rf ./env
	virtualenv -p python3.6 env
	env/bin/pip install -U pip
	pip install -r requirements.txt
