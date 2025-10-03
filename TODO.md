## FAZER ##
0 - validar com Belmonte/Celio se vou poder subir isso no kubernetes em algum cluster de Dev/Homolog (por exemplo)
1 - Preciso finalizar a questão da pipeline de deploy no kubernetes (ver com SRE como estão usando)
 > ter um registry para subir a imagem dentro da XP
 > definir o cluster k8s
  * usar HELM?
 > https para acessar o app (ingress + secrets tls)
 > os dados hoje são salvos em PV (PersistentVolume)
  * será que precisa mudar isso ou não?

2 - preciso pensar sobre o script (parte 1)
 > filtra de arquivo/csv "bruto" do PowerBI
  > e o principal (mais complicado), a parte de autenticar no service now
    para conseguir pegar o Tarefas de Correção de cada alerta
  *  talvez um usuário de serviço (precisarei ajustar script/parte 1)   

3 - to com sono, revisar tudo novamente amanhã (ponto a ponto)