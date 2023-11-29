download:
ifeq (,$(wildcard ./fusion-agent))
	git clone https://${GH_USER}:${GITHUB_PASSWORD}@eos2git.cec.lab.emc.com/ISG-Edge/fusion-agent.git && cd './fusion-agent' && git checkout rel/magicp1-2.0.0 && cd ..
endif
ifeq (,$(wildcard ./fusion-common))
	git clone https://${GH_USER}:${GITHUB_PASSWORD}@eos2git.cec.lab.emc.com/ISG-Edge/fusion-common.git && cd './fusion-common' && git checkout rel/magicp1-2.0.0 && cd ..
endif
ifeq (,$(wildcard ./fusion-manager))
	git clone https://${GH_USER}:${GITHUB_PASSWORD}@eos2git.cec.lab.emc.com/ISG-Edge/fusion-manager.git && cd './fusion-manager' && git checkout rel/magicp1-2.0.0 && cd ..
endif
ifeq (,$(wildcard ./cloudify-utilities-plugins-sdk))
	git clone https://github.com/cloudify-incubator/cloudify-utilities-plugins-sdk.git && cd './cloudify-utilities-plugins-sdk' && git checkout fusion && cd ..
endif
