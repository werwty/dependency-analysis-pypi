#!/usr/bin/env bash

output_dir=$1
worker_id=$2

args=(
  "0      27600  ${output_dir}/worker1"
  "27600  55200  ${output_dir}/worker2"
  "55200  82800  ${output_dir}/worker3"
  "82800  110400 ${output_dir}/worker4"
  "110400 138000 ${output_dir}/worker5"
  "138000 165600 ${output_dir}/worker6"
  "165600 193200 ${output_dir}/worker7"
  "193200 -1     ${output_dir}/worker8"
)

echo Start with command: python3 ./dep_scanner.py "${args[(($1))]}"
echo "${args[(($worker_id))]}" | xargs python3 ./dep_scanner.py 2>&1 | tee "stdout_worker${worker_id}.txt"
