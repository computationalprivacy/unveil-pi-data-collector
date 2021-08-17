#!/bin/bash


until /usr/bin/tshark -i $1 -w $2 $3; do
  echo Transfer disrupted, retrying in 10 seconds...
  sleep 10
done