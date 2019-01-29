#!/bin/bash
tar -zcvf /tmp/data.tar.gz /home/alexandre_yamashita/Workspace/cml/resources

echo "Copying data to server."
ssh ra163124@ssh.students.ic.unicamp.br mkdir -p /tmp/pip/
scp /tmp/data.tar.gz ra163124@ssh.students.ic.unicamp.br:/tmp/pip/

echo "Removing compressed file from host."
rm /tmp/data.tar.gz

echo "Extracting data."
ssh ra163124@ssh.students.ic.unicamp.br tar -zxvf /tmp/pip/data.tar.gz -C /tmp/pip/
ssh ra163124@ssh.students.ic.unicamp.br rm -Rf /tmp/pip/resources
ssh ra163124@ssh.students.ic.unicamp.br mv /tmp/pip/home/alexandre_yamashita/Workspace/cml/resources /tmp/pip/resources

echo "Removing compressed file from server."
ssh ra163124@ssh.students.ic.unicamp.br rm -Rf /tmp/pip/data.tar.gz

echo "Removing extraction directory."
ssh ra163124@ssh.students.ic.unicamp.br rm -Rf /tmp/pip/home

echo "Done."
