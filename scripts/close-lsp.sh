#!/bin/bash
# Exit LSP on nvim exit

#file_type=$(echo $1 | cut -d '.' -f 2)
nvim_editor_count=$(ps ax | grep nvim | awk '/[0-9]\snvim.*/' | wc -l)
#terminal_count=$(ps ax | grep urxvt | awk '/[0-9]\surxvt.*/' | wc -l)

#if [[ $terminal_count -eq 0 ]]; then
#    pkill -f jvm
#fi

#if [[ "$1" =~ .*".java"$ ]] && [[ $nvim_editor_count -eq 1 ]]; then
#    pkill -f jvm
#fi

if [[ "$1" =~ .*".java"$ ]]; then
    pkill -f jvm
fi
