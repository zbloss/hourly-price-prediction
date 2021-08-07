FROM public.ecr.aws/lambda/python:3.8

RUN mkdir /tmp/project

COPY lambda_requirements.txt /tmp/project/lambda_requirements.txt
COPY lambda_function.py /tmp/project/lambda_function.py
COPY hourly_price_prediction /tmp/project/hourly_price_prediction

WORKDIR /tmp/project

RUN pip install -r lambda_requirements.txt

CMD ["lambda_function.lambda_handler"]