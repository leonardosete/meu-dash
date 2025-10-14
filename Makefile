# Makefile Proxy
#
# Este arquivo atua como um proxy para o Makefile.mk.
# Ele garante que o comando `make <target>` funcione diretamente,
# redirecionando a execução para o arquivo Makefile.mk.

# O alvo '%' captura qualquer alvo que não foi explicitamente definido.
# A variável automática '$@' representa o nome do alvo que foi invocado.
%:
	@$(MAKE) -f Makefile.mk $@