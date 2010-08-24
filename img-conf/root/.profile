# ~/.profile: executed by Bourne-compatible login shells.

mesg n

if [ "$SCREENME" ]; then
    screen -list | grep clovr-login
    if [ "$?" == "0" ]; then
	exec screen -s /bin/bash -rd clovr-login	
    else
	exec screen -s /bin/bash -S clovr-login /root/.clovr-login
    fi
fi
export SCREENME=
if [ "$BASH" ]; then
  if [ -f ~/.bashrc ]; then
    . ~/.bashrc
  fi
fi
