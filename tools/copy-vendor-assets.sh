#!/usr/bin/env bash
SOURCE_BASE_PATH="node_modules"
TARGET_BASE_PATH="src/app/static/vendor"

echo - Copying HTMX
mkdir -p ${TARGET_BASE_PATH}/htmx
cp -a ${SOURCE_BASE_PATH}/htmx.org/dist/. ${TARGET_BASE_PATH}/htmx/

echo - Copying Bootstrap Show Password
mkdir -p ${TARGET_BASE_PATH}/bootstrap-show-password
cp -a ${SOURCE_BASE_PATH}/bootstrap-show-password/dist/. ${TARGET_BASE_PATH}/bootstrap-show-password/
