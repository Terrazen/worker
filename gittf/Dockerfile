FROM public.ecr.aws/lambda/python:3.9 as build

ENV PYTHONUNBUFFERED=1
# TODO: make this multistage
RUN pip install --upgrade pip
RUN yum install -y git
RUN git clone --depth=1 https://github.com/tfutils/tfenv.git ~/.tfenv
# TODO: update path for tfenv to work
RUN echo 1
COPY requirements.txt src/requirements.txt
RUN pip install --no-cache-dir -r src/requirements.txt

COPY . src
COPY .env .
CMD [ "src.main.handler" ]