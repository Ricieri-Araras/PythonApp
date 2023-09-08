from flask import Flask, request, redirect, session
from utils import render_page
from flask_mysqldb import MySQL
import bcrypt
import os
from urllib.parse import quote

app = Flask(__name__, template_folder='templates')
app.secret_key = 'my_secret_key'

# Configurações do banco de dados
app.config['MYSQL_HOST'] = 'servidor do banco de dados'
app.config['MYSQL_USER'] = 'usuario do banco '
app.config['MYSQL_PASSWORD'] = 'senha'
app.config['MYSQL_DB'] = 'nome do banco'

# Inicialização do objeto MySQL
mysql = MySQL(app)


######### login ##########

@app.route('/', methods=['GET', 'POST'])
def index():
    return redirect('static/index.html')


@app.route('/mercado', methods=['GET','POST'])
def mercado():
    return render_page('login.html')

# realiza login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        salt = bcrypt.gensalt()
        usuario = request.form['usuario']
        session['username'] = usuario
        senha = request.form['senha']
        if senha is not None:
            hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)

        consulta = "SELECT senha FROM funcionario WHERE usuario = %s"
        valores = (usuario,)
        connection = mysql.connect
        cursor = connection.cursor()
        cursor.execute(consulta, valores)
        resultado = cursor.fetchone()
        cursor.close()
        connection.close()

        if resultado is None:
            mensagem = 'Usuário não encontrado.'
            return render_page('login.html', mensagem=mensagem)
        else:
            senha_armazenada = resultado[0].encode('utf-8')
            if bcrypt.checkpw(senha.encode('utf-8'), senha_armazenada):
                session['usuario'] = usuario  # Armazena o usuário na sessão
                return redirect('/home')
            else:
                mensagem = 'Senha Incorreta.'
                return render_page('login.html', mensagem=mensagem)

    return render_page('login.html')

# realiza o logoff
@app.route('/logout')
def logout():
    session.pop('usuario', None)  # Remove o usuário da sessão
    return redirect('/login')

####### home ########

@app.route('/home')
def home():
    if 'usuario' in session:
        usuario = session['usuario']
        mensagem = session.pop('mensagem', None)  # Recuperar e remover a mensagem da sessão
        return render_page('home.html', usuario=usuario, mensagem=mensagem)
    else:
        return redirect('/login')

########## usuarios ###########

# realiza a consulta de usuarios e chama a pagina para exibir
@app.route('/consultausuarios')
def consultausuarios():
    usuario = session['usuario']
    consulta = "SELECT * FROM funcionario WHERE usuario <> 'master'"
    cursor = mysql.connection.cursor()
    cursor.execute(consulta)
    resultado = cursor.fetchall()

    return render_page('consultausuarios.html', dados=resultado, usuario=usuario)

# chamar pagina de cadastro de usuario
@app.route('/pagecaduser', methods=['GET', 'POST'])
def pagecaduser():
    usuario = session['usuario']
    return render_page('cadastrarusuario.html', usuario=usuario)

# realiza o cadastro de novo usuario
@app.route('/cadastrarusuario', methods=['POST'])
def cadastrarusuario():
    usuario = session['usuario']
    if request.method == 'POST':
        salt = bcrypt.gensalt()
        user = request.form['user']
        senha = request.form['senha']
        if user != 'master':
            if senha is not None:
                hashed_password = bcrypt.hashpw(senha.encode('utf-8'), salt)

                consulta = "INSERT INTO funcionario (usuario, senha) VALUES (%s, %s)"
                valores = (user, hashed_password)
                connection = mysql.connect
                cursor = connection.cursor()
                cursor.execute(consulta, valores)
                connection.commit()
                cursor.close()
                connection.close()

                mensagem = 'Usuário cadastrado com sucesso'
                return render_page('home.html', mensagem=mensagem , usuario = usuario)

        else:

            mensagem = 'Usuário inválido.'
            return render_page('home.html', mensagem=mensagem , usuario = usuario)



####################
#cancelar cadastro de usuario
@app.route('/cancelarcadastrousuario', methods=['GET', 'POST'])
def cancelarcadastrousuario():
    nome = session.get('username')
    return render_page('home.html', usuario=nome)

############# senha ##############

# chama pagina de troca de senha
@app.route('/trocasenha', methods=['GET', 'POST'])
def trocasenha():
    usuario = session['username']
    return render_page('trocasenha.html', usuario=usuario)

######

# realiza a troca da senha
@app.route('/changepassword', methods=['POST'])
def atualizasenha():
    usuario = request.form['usuario']
    session['username'] = usuario
    senha = request.form['senha']
    novasenha = request.form['novasenha']

    if not usuario or not senha or not novasenha:
        mensagem = 'Por favor, preencha todos os campos.'
        return render_page('trocasenha.html', mensagem=mensagem)

    with mysql.connection.cursor() as cursor:
        consulta = "SELECT senha FROM funcionario WHERE usuario = %s"
        valores = (usuario,)
        cursor.execute(consulta, valores)
        resultado = cursor.fetchone()

        if resultado is None:
            mensagem = 'Usuário não encontrado.'
            return render_page('trocasenha.html', mensagem=mensagem)

        senha_armazenada = resultado[0].encode('utf-8')
        if bcrypt.checkpw(senha.encode('utf-8'), senha_armazenada):
            hashed_password = bcrypt.hashpw(novasenha.encode('utf-8'), bcrypt.gensalt())

            sql = "UPDATE funcionario SET senha = %s WHERE usuario = %s"
            valores = (hashed_password, usuario)
            cursor.execute(sql, valores)
            mysql.connection.commit()

            mensagem = 'Senha alterada com sucesso.'
            return redirect('/home')
        else:
            mensagem = 'Senha atual incorreta'
            return render_page('trocasenha.html', mensagem=mensagem)

# cancela a troca de senha
@app.route('/cancelatrocasenha', methods=['GET', 'POST'])
def cancelatrocasenha():
    nome = session['usuario']
    return render_page('home.html', usuario=nome)

####### Produto ##########

# chamar pagina de cadastrar produto
@app.route('/pagecadproduct', methods=['GET', 'POST'])
def pagecadproduct():
    usuario = session['username']
    query = "select codigo_barras from produtos"
    cursor = mysql.connection.cursor()
    cursor.execute(query)
    resultado = cursor.fetchall()

    return render_page('cadastrarproduto.html', dados=resultado, usuario=usuario)

# realiza o cadastro de produtos e chama a pagina para exibir
@app.route('/cadastraproduto', methods=['GET', 'POST'])
def cadastraproduto():
    usuario = session['username']
    # Recebimento dos dados da requisição POST
    descricao = request.form['descricao']
    setor = request.form['setor']

    try:
        preco = float(request.form['preco'])
    except ValueError:
        mensagem = "O campo 'preco' deve ser um número válido."
        return render_page('cadastrarproduto.html', mensagem=mensagem , usuario=usuario)

    codigo_barras = request.form['codigo_barras']

    if not (descricao or setor or preco or codigo_barras):
        mensagem = "Todos os campos são obrigatórios. Exceto imagem!"
        return render_page('cadastrarproduto.html', mensagem=mensagem, usuario=usuario)

    if (request.form['descricao']) is not None:
        file = request.files['imagem']
        if file.filename != '':
            file = request.files['imagem']
            # Salvar o arquivo na pasta /static/image
            filename = file.filename
            file.save(os.path.join('static/image', filename))
            # Obter o nome da imagem
            nome_imagem = filename

        else:
            nome_imagem = ""

    # Verificar se o código de barras ou a descrição já existem
    consulta = "SELECT * FROM produtos WHERE descricao = %s or codigo_barras = %s"
    valores = (descricao, codigo_barras)

    with mysql.connection.cursor() as cursor:
        cursor.execute(consulta, valores)
        resultado = cursor.fetchone()

    if resultado :

        mensagem = "Produto já existe!"
        return render_page('cadastrarproduto.html', mensagem=mensagem, usuario=usuario)

    else:
        # Se não houver resultado, você pode prosseguir com a inserção dos dados
        with mysql.connection.cursor() as cursor:
            sql = "INSERT INTO produtos (descricao, setor, preco, codigo_barras, ativo, nome_imagem) VALUES (%s, %s, %s, %s, %s, %s)"
            ativo = 1
            valores = (descricao, setor, preco, codigo_barras, ativo, nome_imagem)
            cursor.execute(sql, valores)
            mysql.connection.commit()
            cursor.close()

    # Retornar para a pagina de consulta de produtos
    mensagem = "Produto cadastrado com sucesso"
    return render_page('home.html', mensagem=mensagem, usuario=usuario)


################## Consultas #############################

# chama consulta de usuario
@app.route('/consultauser', methods=['GET', 'POST'])
def consultauser():
    usuario = session['username']

    return render_page('consultausuario.html', usuario=usuario)

###########


# consulta para exclusão de usuario
@app.route('/apagaruser', methods=['GET', 'POST'])
def apagaruser():
    usuario = session['username']
    parte = request.form['user']

    consulta = "SELECT * FROM funcionario WHERE usuario LIKE %s and usuario <> 'master' "
    valores = ('%' + parte + '%',)
    cursor = mysql.connection.cursor()
    cursor.execute(consulta, valores)
    resultado = cursor.fetchall()

    if resultado:
        return render_page('consultausuarioexclusao.html',dados=resultado, usuario=usuario)

    else:

        mensagem='Usuário não encontrado.'
        return render_page('consultausuario.html', mensagem=mensagem, usuario=usuario)

###########

# realiza a consulta de produtos e chama a pagina para exibir
@app.route('/consultaprodutos')
def consultaprodutos():
    usuario = session['username']
    consulta = "SELECT * FROM produtos  WHERE ativo = 1;"
    cursor = mysql.connection.cursor()
    cursor.execute(consulta)
    resultado = cursor.fetchall()

    return render_page('consultaprodutos.html', dados=resultado, usuario=usuario)

##########
# inserir codigo para realizar a consulta de produto por codigo
@app.route('/consultacodigo',methods=['GET', 'POST'])
def consultacodigo():
    usuario = session['username']
    return render_page('consultacodigo.html', usuario=usuario)

#########
# inserir codigo para realizar a consulta de produto por descrição
@app.route('/consultaprodutodescricao',methods=['GET', 'POST'])
def consultaprodutodescricao():
    usuario = session['username']
    return render_page('consultaprodutodescricao.html', usuario=usuario)

###########

# inserir codigo para realizar a consulta de produto por codigo
@app.route('/consultaexclusao',methods=['GET', 'POST'])
def consultaexclusao():
    usuario = session['username']
    return render_page('consultaexclusao.html', usuario=usuario)

###########

# realiza a consulta de produto por codigo
@app.route('/consultaprodutounico',methods=['GET', 'POST'])
def consultaprodutounico():
    usuario = session['username']
    consulta = "SELECT * FROM produtos  WHERE codigo_barras = %s and ativo = 1"
    codigo = request.form['codigo_barras']
    valor = (codigo,)
    cursor = mysql.connection.cursor()
    cursor.execute(consulta, valor)
    resultado = cursor.fetchall()

    return render_page('consultaprodutounico.html', produto=resultado , usuario=usuario)

##########

# realiza a consulta de produtos e chama a pagina para exibir
@app.route('/exibirprodutodescricao', methods=['GET', 'POST'])
def exibirprodutodescricao():
    usuario = session['username']
    consulta = "SELECT * FROM produtos WHERE descricao like %s and ativo = 1;"
    parte = request.form['descricao']
    valores = ('%' + parte + '%',)
    cursor = mysql.connection.cursor()
    cursor.execute(consulta, valores)
    resultado = cursor.fetchall()

    if resultado:
        return render_page('exibirprodutodescricao.html', dados=resultado, usuario=usuario)
    else:

        mensagem = "Produto(s) não encontrado(s)."
        return render_page('consultaprodutodescricao.html', mensagem=mensagem, usuario=usuario)

##########

@app.route('/consultacodigo2',methods=['GET', 'POST'])
def consultacodigo2():
    usuario = session['username']
    return render_page('consultacodigo2.html', usuario=usuario)

#########

@app.route('/alterarprecolote')
def alterarprecolote():
    usuario = session['username']
    consulta = "SELECT DISTINCT setor FROM produtos WHERE ativo = 1"

    with mysql.connection.cursor() as cursor:
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()

    return render_page('alterarpreco.html', setores=resultado, usuario=usuario)

#########

# realiza a consulta de produtos e chama a pagina para exibir produtos descontinuados
@app.route('/produtosdesativados')
def produtosdesativados():
    usuario = session['username']
    consulta = "SELECT * FROM produtos  WHERE ativo = 0"
    contagem = "SELECT count(*) FROM produtos  WHERE ativo = 0"

    with mysql.connection.cursor() as cursor:
        cursor.execute(consulta)
        resultado = cursor.fetchall()
        cursor.close()

    with mysql.connection.cursor() as cursor2:
        cursor2.execute(contagem)
        resultado2 = cursor2.fetchone()
        numero_de_produtos_desativados = resultado2[0]
        cursor2.close()

    return render_page('produtosdesativados.html', dados=resultado , total=numero_de_produtos_desativados, usuario=usuario)

################## Consultas para Alterações #############################

# realiza a consulta para alteração de produtos ativos
@app.route('/alterar_produto', methods=['GET', 'POST'])
def alterar_produto():
    usuario = session['username']
    consulta = "SELECT * FROM produtos WHERE codigo_barras = %s and ativo = 1"
    codigo_barras = request.form['codigo_barras']
    valores = (codigo_barras,)

    endereco = "SELECT nome_imagem FROM produtos WHERE codigo_barras = %s and ativo = 1"


    with mysql.connection.cursor() as cursor:
        cursor.execute(consulta, valores)
        resultado = cursor.fetchone()

    # Obtém o nome da imagem do resultado da consulta
    with mysql.connection.cursor() as cursor2:
        cursor2.execute(endereco, valores)
        resultado2 = cursor2.fetchone()
        if resultado2 is not None:
            nome_imagem = resultado2[0]
        else:
            # Tratar o caso em que não há resultado disponível
            nome_imagem = None  # ou algum valor padrão, se preferir     if resultado2 is not None:

    if resultado:

        if nome_imagem is not None:
            # Construa o caminho completo da imagem
            nome_imagem_encoded = quote(nome_imagem)
            caminho_imagem = "/static/image/" + nome_imagem_encoded


            return render_page('alterarproduto.html', produto=resultado, caminho_imagem=caminho_imagem, usuario=usuario)

        else:

            mensagem = 'Não foi possivel carregar a imagem.'
            return render_page('alterarproduto.html', produto=resultado, mensagem=mensagem, usuario=usuario)

    else:
        mensagem = "Código de barras não cadastrado."
        return render_page('consultacodigo2.html', produto=resultado, mensagem=mensagem, usuario=usuario)

#####  fim do codigo



################## Realiza Alterações #############################

# realiza alteração de produtos ativados
@app.route('/altera_produto', methods=['GET', 'POST'])
def altera_produto():
    usuario = session['username']
    # Obter os dados do formulário
    id = request.form['id']
    descricao = request.form['descricao']
    setor = request.form['setor']

    if not (descricao and setor):
        mensagem = "Campos Descrição e Setor são obrigatórios. Exceto imagem!"
        return render_page('cadastrarproduto.html', mensagem=mensagem, usuario=usuario)

    if 'imagem' in request.files:
        file = request.files['imagem']
        if file.filename != '':
            file = request.files['imagem']
            # Salvar o arquivo na pasta /static/image
            filename = file.filename
            file.save(os.path.join('static/image', filename))

            # Obter o nome da imagem
            nome_imagem = filename

            # Atualizar os valores descrição, setor e nome da imagem no banco de dados na posição do registro
            sql = "UPDATE produtos SET descricao = %s, setor = %s, nome_imagem = %s WHERE id = %s"
            valores = (descricao, setor, nome_imagem, id)

            with mysql.connection.cursor() as cursor:
                cursor.execute(sql, valores)
                mysql.connection.commit()
                cursor.close()

        mensagem = "Produto alterado com sucesso."
        return render_page('/home.html' , mensagem=mensagem, usuario=usuario)

    else:
        sql = "UPDATE produtos SET descricao = %s, setor = %s WHERE id = %s"
        valores = (descricao, setor, id)

        with mysql.connection.cursor() as cursor:
            cursor.execute(sql, valores)
            mysql.connection.commit()
            cursor.close()

            mensagem = "Produto alterado com sucesso."
            return render_page('/home.html' , mensagem=mensagem, usuario=usuario)

###################

# realiza a alteração de preco de produto
@app.route('/altera_preco', methods=['GET', 'POST'])
def alterapreco():
    usuario = session['username']
    id = request.form['id']
    preco = float(request.form['preco'])

    # Atualizar os valores no banco de dados
    sql = "UPDATE produtos SET preco = %s WHERE id = %s"
    valores = (preco, id)

    with mysql.connection.cursor() as cursor:
        cursor.execute(sql, valores)
        mysql.connection.commit()

    cursor.close()
    mensagem = "Preço do Produto alterado com sucesso."
    return render_page('home.html' , mensagem=mensagem, usuario=usuario)

##########

# realiza a alteração de produtos reativando produto desativados
@app.route('/alterar_desativado', methods=['GET', 'POST'])
def alterar_desativado():
    usuario = session['username']
    id = request.form['id']
    sql = "UPDATE produtos SET ativo = 1 WHERE id = %s"
    valores = (id,)
    with mysql.connection.cursor() as cursor:
        cursor.execute(sql, valores)
        mysql.connection.commit()

    # Recupera os dados atualizados do banco de dados
    with mysql.connection.cursor() as cursor:
        consulta = "SELECT * FROM produtos WHERE ativo = 0;"
        cursor.execute(consulta)
        resultado = cursor.fetchall()

    mensagem = "Produto reativado com sucesso."
    return render_page('produtosdesativados.html', dados=resultado, mensagem=mensagem, usuario=usuario)

##########

@app.route('/altera_preco_lote', methods=['GET', 'POST'])
def alteralote():
    usuario = session['username']
    setor = request.form['setor']
    tipo = request.form['tipo']
    ajuste = float(request.form['ajuste'])

    if setor == "Todos":
        consulta = "SELECT id, preco FROM produtos WHERE ativo = 1"

        with mysql.connection.cursor() as cursor:
            cursor.execute(consulta)
            resultado = cursor.fetchall()

    else:
        consulta = "SELECT id, preco FROM produtos WHERE ativo = 1 and setor = %s"
        valor=(setor,)

        with mysql.connection.cursor() as cursor:
            cursor.execute(consulta, valor)
            resultado = cursor.fetchall()

    for produto in resultado:
        id, preco = produto
        if tipo == "valor":
            preco = float(preco) + ajuste
        elif tipo == "porcentagem":
            preco = float(preco) + (float(preco) * ajuste/100)

        sql = "UPDATE produtos SET preco = %s WHERE id = %s"
        valores = (preco, id)

        with mysql.connection.cursor() as cursor:
            cursor.execute(sql, valores)
            mysql.connection.commit()

    mensagem = "Preços Atualizados."
    return render_page('home.html', mensagem=mensagem, usuario=usuario)


################ Preparar Exclusão ###########3

#consultar produtos para exclusão
@app.route('/produto_para_exclusao', methods=['GET', 'POST'])
def produto_exclusao():
    usuario = session['username']
    parte = request.form['descricao']

    consulta = "SELECT * FROM produtos where descricao LIKE %s and ativo = 1"
    total = "SELECT COUNT(*) FROM produtos where descricao LIKE %s and ativo = 1"
    valores = ('%' + parte + '%',)

    with mysql.connection.cursor() as cursor:
        cursor.execute(consulta, valores)
        resultado = cursor.fetchall()

    with mysql.connection.cursor() as cursor2:
        cursor2.execute(total, valores)
        total_registros= cursor2.fetchall()

    if len(resultado) == 0:
        mensagem = "Produto não encontrado."
        return render_page("home.html", mensagem=mensagem, usuario=usuario)

    mensagem = "Produto(s) encontrado(s)."
    return render_page("Home.html", mensagem=mensagem, dados=resultado, total=total_registros, usuario=usuario)


################## Realiza Exclusões #############################

#excluir usuario
@app.route('/excluir_user', methods=['GET', 'POST'])
def excluir_user():
    usuario = session['username']
    id = request.form['id']
    sql_exclusao = "DELETE FROM funcionario WHERE id = %s and usuario <> 'master'"
    cursor = mysql.connection.cursor()
    cursor.execute(sql_exclusao, (id,))
    mysql.connection.commit()

    mensagem = "Usuário excluído com sucesso."

    return render_page('home.html', usuario=usuario, mensagem=mensagem)

################

# realiza a exclusão do produto
@app.route('/excluir_produto/<int:produto_id>')
def excluir_produto(produto_id):
    usuario = session['username']
    # Realiza a exclusão do produto no banco de dados
    sql_exclusao = "UPDATE produtos SET ativo = 0 WHERE id = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(sql_exclusao, (produto_id,))
    mysql.connection.commit()

    mensagem = "Produto excluído com sucesso."

    # Recupera os dados atualizados do banco de dados
    with mysql.connection.cursor() as cursor:
        consulta = "SELECT * FROM produtos WHERE ativo = 1;"
        cursor.execute(consulta)
        resultado = cursor.fetchall()

    # Renderiza o template 'consultaprodutos.html' com os dados atualizados
    return render_page('consultaprodutos.html', dados=resultado, mensagem=mensagem, usuario=usuario)

##############

# realiza a exclusão do produto por codigo de barras
@app.route('/excluir_cod_barras', methods=['GET', 'POST'])
def excluir_cod_barras():
    usuario = session['username']
    cod = request.form['codigo_barras']

    try:
        # Realiza a exclusão do produto no banco de dados
        sql_exclusao = "UPDATE produtos SET ativo = 0 WHERE codigo_barras = %s"
        value = (cod,)
        cursor = mysql.connection.cursor()
        cursor.execute(sql_exclusao, value)
        mysql.connection.commit()

        mensagem = "Produto excluído com sucesso."

        # Renderiza o template 'consultaprodutos.html' com os dados atualizados
        return render_page('home.html', mensagem=mensagem, usuario=usuario)

    except:
        mensagem = "Produto não encontrado."
        return render_page("home.html", mensagem=mensagem, usuario=usuario)



###############

# realiza a exclusão do produto por descricao
@app.route('/excluir_produto_/<int:produto_id>')
def excluir_produto_descricao(produto_id):
    usuario = session['username']
    # Realiza a exclusão do produto no banco de dados
    sql_exclusao = "UPDATE produtos SET ativo = 0 WHERE id = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(sql_exclusao, (produto_id,))
    mysql.connection.commit()

    mensagem = "Produto excluído com sucesso."

    # Renderiza o template 'consultaprodutos.html' com os dados atualizados
    return render_page('home.html', mensagem=mensagem, usuario=usuario)


##############

#excluir lotes
@app.route('/excluir_lotes', methods=['GET', 'POST'])
def excluir_produtos_inativos():
    usuario = session['username']
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM produtos WHERE ativo = 0")
    mysql.connection.commit()

    # Renderiza o template 'consultaprodutos.html' com os dados atualizados
    return render_page('produtosdesativados.html', usuario=usuario)


# inicialização do app na porta 6000
if __name__ == '__main__':
    app.run(port=6000)



