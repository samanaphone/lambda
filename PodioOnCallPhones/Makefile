FUNCTION_NAME=$(lastword $(subst /, ,$(shell pwd)))
PACKAGE_PATH=$(shell pwd)
CONF_PATH=$(PACKAGE_PATH)/../etc
ARN=$(shell cat $(CONF_PATH)/role_arn.txt)
TIMEOUT=$(shell cat $(CONF_PATH)/timeout.txt)
VARIABLES=$(shell cat $(CONF_PATH)/variables.txt)

$(FUNCTION_NAME): lib/pypodio2
	zip -r $(FUNCTION_NAME).zip * -x Makefile $(FUNCTION_NAME).zip

install: $(FUNCTION_NAME)
	aws lambda update-function-code --function-name $(FUNCTION_NAME) --zip-file fileb://$(PACKAGE_PATH)/$(FUNCTION_NAME).zip

clean:
	rm -Rf lib
	rm -f $(FUNCTION_NAME).zip

lib:
	mkdir lib

lib/pypodio2: lib
	python3 -m pip install git+https://github.com/podio/podio-py.git@master -t lib

config:
	aws lambda update-function-configuration \
          --function-name $(FUNCTION_NAME) \
          --role "$(ARN)" \
          --handler "lambda_function.lambda_handler" \
          --description "" \
          --timeout $(TIMEOUT) \
          --memory-size 128 \
          --vpc-config "{\"SubnetIds\":[],\"SecurityGroupIds\":[]}" \
          --environment $(VARIABLES) \
          --runtime "python3.11" \
          --tracing-config Mode="PassThrough"

print:
	echo $(FUNCTION_NAME)
	echo $(PACKAGE_PATH)
	echo $(ARN)
	echo $(TIMEOUT)
	echo $(VARIABLES)

