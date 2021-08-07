FROM public.ecr.aws/lambda/python:3.8

COPY lambda_requirements.txt ./
COPY lambda_function.py ./

RUN mkdir hourly_price_prediction

COPY hourly_price_prediction/data/s3_helper.py ./hourly_price_prediction/data/s3_helper.py
COPY hourly_price_prediction/models/asset_trader.py ./hourly_price_prediction/models/asset_trader.py

RUN touch ./hourly_price_prediction/__init__.py && \
    touch ./hourly_price_prediction/data/__init__.py && \
    touch ./hourly_price_prediction/models/__init__.py

RUN pip install -r lambda_requirements.txt

RUN export PYTHONPATH=$PYTHONPATH:./hourly_price_prediction

CMD ["lambda_function.lambda_handler"]