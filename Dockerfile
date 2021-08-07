FROM public.ecr.aws/lambda/python:3.8

COPY lambda_requirements.txt lambda_requirements.txt
COPY lambda_function.py lambda_function.py
COPY hourly_price_prediction hourly_price_prediction

RUN pip install -r lambda_requirements.txt

CMD ["lambda_function.lambda_handler"]