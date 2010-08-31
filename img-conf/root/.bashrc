# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

export TERMCAP=

# If not running interactively, don't do anything
[ -z "$PS1" ] && return

case "$-" in
*i*)	;;
*)	return 
esac

# don't put duplicate lines in the history. See bash(1) for more options
#export HISTCONTROL=ignoredups

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "$debian_chroot" -a -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

#Wait for vappio setup to complete
#This will spin at login until we leave pending state
#Ctrl-C this loop is harmless but image will not be ready for use
if [ -f "/opt/vappio-scripts/vappio_config.sh" ]
then
    source /opt/vappio-scripts/vappio_config.sh

    if [ -f "$vappio_runtime/node_type" ]; then
	nodetype=`cat $vappio_runtime/node_type`;
    else
	nodetype="PENDING"
    fi
    
    #Wait for vappio boot process to complete
    if [ "$nodetype" = 'PENDING' ]
    then
	echo -n "Node is $nodetype. Waiting for setup to finish."
	wait=1
    fi
    hostn=`hostname`
    while [ "$nodetype" = 'PENDING' ] || [ "hostn" = "(none)" ]
    do
	echo -n '.'
	if [ -f "$vappio_runtime/node_type" ]
	then
	    nodetype=`cat $vappio_runtime/node_type`
	fi
	sleep 1
    done 
    echo 
    if [ -f "$vappio_runtime/node_type" ]
    then
	nodetype=`cat $vappio_runtime/node_type`;
    fi
    if [ -f "$vappio_runtime/cloud_type" ]
    then
	cloudtype=`cat $vappio_runtime/cloud_type`;
    fi
fi
hostn=`hostname`

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
xterm-color)
    PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '
    ;;
*)
    PS1='$cloudtype $nodetype $hostn \w\$ '
    ;;
esac
# Comment in the above and uncomment this below for a color prompt
#PS1='${debian_chroot:+($debian_chroot)}\[\033[01;32m\]\u@\h\[\033[00m\]:\[\033[01;34m\]\w\[\033[00m\]\$ '

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PROMPT_COMMAND='echo -ne "\033]0;${USER}@${HOSTNAME}: ${PWD/$HOME/~}\007"'
    ;;
*)
    ;;
esac

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

#if [ -f ~/.bash_aliases ]; then
#    . ~/.bash_aliases
#fi

# enable color support of ls and also add handy aliases
if [ "$TERM" != "dumb" ]; then
    eval "`dircolors -b`"
    alias ls='ls --color=auto'
    #alias dir='ls --color=auto --format=vertical'
    #alias vdir='ls --color=auto --format=long'
fi

# some more ls aliases
#alias ll='ls -l'
#alias la='ls -A'
#alias l='ls -CF'

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
#if [ -f /etc/bash_completion ]; then
#    . /etc/bash_completion
#fi

# Warn before overwrite
alias mv='mv -i'
alias cp='cp -i'
alias l='ls -l'

# Source vappio envs
source /opt/vappio-scripts/vappio_config.sh

source /root/clovrEnv.sh

PATH=$PATH:./
