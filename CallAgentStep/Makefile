FUNCTION_NAME=$(lastword $(subst /, ,$(shell pwd)))
PACKAGE_PATH=$(shell pwd)
CONF_PATH=$(PACKAGE_PATH)/../etc
ARN=$(shell cat $(CONF_PATH)/role_arn.txt)
TIMEOUT=$(shell cat $(CONF_PATH)/timeout.txt)
VARIABLES=$(shell cat $(CONF_PATH)/variables.txt)

$(FUNCTION_NAME):
	zip -r $(FUNCTION_NAME).zip * -x Makefile $(FUNCTION_NAME).zip

install: $(FUNCTION_NAME)
	aws lambda update-function-code --function-name $(FUNCTION_NAME) --zip-file fileb://$(PACKAGE_PATH)/$(FUNCTION_NAME).zip

clean:
	rm -f $(FUNCTION_NAME).zip

config:
	aws lambda update-function-configuration \
          --function-name $(FUNCTION_NAME) \
          --role "$(ARN)" \
          --handler "lambda_function.handler" \
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

