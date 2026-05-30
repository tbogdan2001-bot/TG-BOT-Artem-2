@echo off
title Compiler
chcp 65001 > nul
cd /d "%~dp0"
python build_bot.py
pause
