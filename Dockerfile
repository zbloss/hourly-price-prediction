FROM public.ecr.aws/lambda/python:3.8

COPY lambda_requirements.txt ./
COPY lambda_function.py ./

RUN mkdir hourly_price_prediction

COPY hourly_price_prediction/data/__init__.py ./hourly_price_prediction/data/__init__.py
COPY hourly_price_prediction/data/s3_helper.py ./hourly_price_prediction/data/s3_helper.py
COPY hourly_price_prediction/models/asset_trader.py ./hourly_price_prediction/models/asset_trader.py

RUN pip install -r lambda_requirements.txt

CMD ["lambda_function.lambda_handler"]