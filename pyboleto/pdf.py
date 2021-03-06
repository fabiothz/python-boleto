# -*- coding: utf-8 -*-
"""
    pyboleto.pdf
    ~~~~~~~~~~~~

    Classe Responsável por fazer o output do boleto em pdf usando Reportlab.

    :copyright: © 2011 - 2012 by Eduardo Cereto Carvalho
    :license: BSD, see LICENSE for more details.

"""
import os

from reportlab.graphics.barcode.common import I2of5
from reportlab.lib.colors import black
from reportlab.lib.pagesizes import A4, landscape as pagesize_landscape
from reportlab.lib.units import mm, cm
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from .utils import doc_label

class BoletoPDF(object):
    """Geração do Boleto em PDF

    Esta classe é responsável por imprimir o boleto em PDF.
    Outras classes podem ser implementadas no futuro com a mesma interface,
    para fazer output em HTML, LaTeX, ...

    Esta classe pode imprimir boletos em formato de carnê (2 boletos por
    página) ou em formato de folha cheia.

    :param file_descr: Um arquivo ou *file-like* class.
    :param landscape: Formato da folha. Usar ``True`` para boleto
        tipo carnê.

    """
    # pylint: disable=too-many-instance-attributes

    def __init__(self, file_descr, carne=False, title='Boleto'):
        self.width = 155 * mm if carne else 190 * mm
        self.width_canhoto = 40 * mm
        self.height_line = 5.5 * mm if carne else 6.5 * mm
        self.space = 2
        self.font_size_title = 5 if carne else 6
        self.font_size_value = 6 if carne else 9
        self.delta_title = self.height_line - (self.font_size_title + 1)
        self.delta_font = self.font_size_value + 1

        self.carne = carne
        self.pdf_canvas = canvas.Canvas(file_descr, pagesize=A4)
        self.pdf_canvas.setStrokeColor(black)
        self.pdf_canvas.setTitle(title)

    def _draw_recibo_sacado_canhoto(self, boleto_dados, x, y):
        """Imprime o Recibo do Sacado para modelo de carnê

        :param boleto_dados: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boleto_dados: :class:`pyboleto.data.BoletoData`
        :param x: Current X coordinate
        :param y: Current Y coordinate

        """

        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        linha_inicial = 10

        # Horizontal Lines
        self.pdf_canvas.setLineWidth(2)
        self.__horizontalLine(0, 0, self.width_canhoto)

        self.pdf_canvas.setLineWidth(1)
        self.__horizontalLine(0, (1 * self.height_line), self.width_canhoto)
        self.__horizontalLine(0,
                              (linha_inicial + 0) * self.height_line,
                              self.width_canhoto)
        self.__horizontalLine(0,
                              (linha_inicial + 1) * self.height_line,
                              self.width_canhoto)
        self.__horizontalLine(0,
                              (linha_inicial + 2) * self.height_line,
                              self.width_canhoto)

        self.pdf_canvas.setLineWidth(2)
        self.__horizontalLine(0,
                              (linha_inicial + 4.1) * self.height_line,
                              self.width_canhoto)

        # Vertical Lines
        self.pdf_canvas.setLineWidth(1)
        self.__verticalLine(self.width_canhoto - (18 * mm),
                            (linha_inicial + 0) * self.height_line,
                            self.height_line)
        self.__verticalLine(self.width_canhoto - (18 * mm),
                            (linha_inicial + 1) * self.height_line,
                            self.height_line)

        self.pdf_canvas.setFont('Helvetica-Bold', 6)
        self.pdf_canvas.drawString(self.space, 1 * self.height_line + 3, 'Pagador')

        # Titles
        self.pdf_canvas.setFont('Helvetica', 6)
        self.delta_title = self.height_line - (6 + 1)

        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 0) * self.height_line)) + self.delta_title,
            'Nosso Número'
        )
        self.pdf_canvas.drawString(
            self.width_canhoto - (18 * mm) + self.space,
            (((linha_inicial + 0) * self.height_line)) + self.delta_title,
            'Vencimento'
        )
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'Agência/Beneficiário'
        )
        self.pdf_canvas.drawString(
            self.width_canhoto - (18 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'Valor Documento'
        )
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 3) * self.height_line)) + self.delta_title,
            'Beneficiário'
        )

        self.pdf_canvas.setFont('Helvetica-Bold', 10)
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 3.7) * self.height_line)) + self.delta_title,
            'RECIBO DO PAGADOR'
        )

        # Values
        self.pdf_canvas.setFont('Helvetica', 6)
        heigh_font = 9 + 1

        valor_documento = self._formataValorParaExibir(
            boleto_dados.valor_documento
        )

        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 0) * self.height_line)) + self.space,
            boleto_dados.format_nosso_numero()
        )
        self.pdf_canvas.drawString(
            self.width_canhoto - (18 * mm) + self.space,
            (((linha_inicial + 0) * self.height_line)) + self.space,
            boleto_dados.data_vencimento.strftime('%d/%m/%Y')
        )
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            boleto_dados.agencia_conta_cedente
        )
        self.pdf_canvas.drawString(
            self.width_canhoto - (18 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            valor_documento
        )
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 2) * self.height_line)) + self.space,
            '{}: {}'.format(doc_label(boleto_dados.cedente_documento),
                            boleto_dados.cedente_documento)
        )

        cedente_nome_split = boleto_dados.cedente.split(' ')
        cedente_nome1 = ''
        cedente_nome2 = ''
        while len(cedente_nome_split) > 0:
            nome = cedente_nome_split.pop(0)
            sw1 = self.pdf_canvas.stringWidth(cedente_nome1 + nome)
            sw2 = self.pdf_canvas.stringWidth(cedente_nome2 + nome)
            if sw1 < self.width_canhoto and cedente_nome2 == '':
                cedente_nome1 += ' ' + nome
            elif sw2 < self.width_canhoto:
                cedente_nome2 += ' ' + nome
            else:
                cedente_nome2 += '...'
                break

        cedente_nome1 = cedente_nome1.strip()
        cedente_nome2 = cedente_nome2.strip()

        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 3) * self.height_line)) + self.space,
            cedente_nome1
        )
        self.pdf_canvas.drawString(
            self.space,
            (((linha_inicial + 2.5) * self.height_line)) + self.space,
            cedente_nome2
        )

        self.pdf_canvas.drawString(
            self.space, (7.5 + self.space),
            boleto_dados.sacado_nome[:34]
        )

        self.pdf_canvas.drawString(
            self.space, (0.5 + self.space),
            '{}: {}'.format(doc_label(boleto_dados.sacado_documento),
                            boleto_dados.sacado_documento)
        )

        demonstrativo = boleto_dados.demonstrativo[0:12]
        for index, value in enumerate(demonstrativo):
            self.pdf_canvas.drawString(
                2 * self.space,
                (linha_inicial - 1) * self.height_line - (index * heigh_font),
                value[0:55]
            )

        self.pdf_canvas.restoreState()

        return (self.width_canhoto,
                ((linha_inicial + 5) * self.height_line))

    def _drawReciboSacado(self, boleto_dados, x, y):
        """Imprime o Recibo do Sacado para modelo de página inteira

        :param boleto_dados: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boleto_dados: :class:`pyboleto.data.BoletoData`

        """

        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        linha_inicial = 15

        # Horizontal Lines
        self.pdf_canvas.setLineWidth(1)
        self.__horizontalLine(0,
                              (linha_inicial + 0) * self.height_line,
                              self.width)
        self.__horizontalLine(0,
                              (linha_inicial + 1) * self.height_line,
                              self.width)
        self.__horizontalLine(0,
                              (linha_inicial + 2) * self.height_line,
                              self.width)

        self.pdf_canvas.setLineWidth(2)
        self.__horizontalLine(0,
                              (linha_inicial + 3) * self.height_line,
                              self.width)

        # Vertical Lines
        self.pdf_canvas.setLineWidth(1)
        self.__verticalLine(
            self.width - (30 * mm),
            (linha_inicial + 0) * self.height_line,
            3 * self.height_line
        )
        self.__verticalLine(
            self.width - (30 * mm) - (35 * mm),
            (linha_inicial + 1) * self.height_line,
            2 * self.height_line
        )
        self.__verticalLine(
            self.width - (30 * mm) - (35 * mm) - (40 * mm),
            (linha_inicial + 1) * self.height_line,
            2 * self.height_line
        )

        # Head
        self.pdf_canvas.setLineWidth(2)
        self.__verticalLine(40 * mm,
                            (linha_inicial + 3) * self.height_line,
                            self.height_line)
        self.__verticalLine(60 * mm,
                            (linha_inicial + 3) * self.height_line,
                            self.height_line)

        if boleto_dados.logo_image:
            logo_image_path = load_image(boleto_dados.logo_image)
            self.pdf_canvas.drawImage(
                logo_image_path,
                0, (linha_inicial + 3) * self.height_line + 3,
                40 * mm,
                self.height_line,
                preserveAspectRatio=True,
                anchor='sw'
            )
        self.pdf_canvas.setFont('Helvetica-Bold', 18)
        self.pdf_canvas.drawCentredString(
            50 * mm,
            (linha_inicial + 3) * self.height_line + 3,
            boleto_dados.codigo_dv_banco
        )
        self.pdf_canvas.setFont('Helvetica-Bold', 11.5)
        self.pdf_canvas.drawRightString(
            self.width,
            (linha_inicial + 3) * self.height_line + 3,
            'Recibo do Pagador'
        )

        # Titles
        self.pdf_canvas.setFont('Helvetica', 6)
        self.delta_title = self.height_line - (6 + 1)

        self.pdf_canvas.drawRightString(
            self.width,
            self.height_line,
            'Autenticação Mecânica'
        )

        self.pdf_canvas.drawString(
            0,
            (((linha_inicial + 2) * self.height_line)) + self.delta_title,
            'Beneficiário'
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) - (40 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.delta_title,
            'Agência/Código Beneficiário'
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.delta_title,
            'CPF/CNPJ Beneficiário'
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.delta_title,
            'Vencimento'
        )

        self.pdf_canvas.drawString(
            0,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'Pagador')
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) - (40 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'Nosso Número')
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'N. do documento')
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.delta_title,
            'Data Documento'
        )

        self.pdf_canvas.drawString(
            0,
            (((linha_inicial + 0) * self.height_line)) + self.delta_title,
            'Endereço Beneficiário'
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 0) * self.height_line)) + self.delta_title,
            'Valor Documento'
        )

        self.pdf_canvas.drawString(
            0,
            (((linha_inicial + 0) * self.height_line - 3 * cm)) +
            self.delta_title,
            'Demonstrativo'
        )

        # Values
        self.pdf_canvas.setFont('Helvetica', 9)
        heigh_font = 9 + 1

        self.pdf_canvas.drawString(
            0 + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.space,
            boleto_dados.cedente
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) - (40 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.space,
            boleto_dados.agencia_conta_cedente
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.space,
            boleto_dados.cedente_documento
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 2) * self.height_line)) + self.space,
            boleto_dados.data_vencimento.strftime('%d/%m/%Y')
        )

        # Take care of long field
        sacado0 = boleto_dados.sacado[0]
        while (stringWidth(sacado0,
                           self.pdf_canvas._fontname,
                           self.pdf_canvas._fontsize
                           ) > 8.4 * cm):

            # sacado0 = sacado0[:-2] + u'\u2026'
            sacado0 = sacado0[:-4] + u'...'

        self.pdf_canvas.drawString(
            0 + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            sacado0
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) - (40 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            boleto_dados.format_nosso_numero()
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) - (35 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            boleto_dados.numero_documento
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 1) * self.height_line)) + self.space,
            boleto_dados.data_documento.strftime('%d/%m/%Y')
        )

        valor_documento = self._formataValorParaExibir(
            boleto_dados.valor_documento
        )

        self.pdf_canvas.drawString(
            0 + self.space,
            (((linha_inicial + 0) * self.height_line)) + self.space,
            boleto_dados.cedente_endereco
        )
        self.pdf_canvas.drawString(
            self.width - (30 * mm) + self.space,
            (((linha_inicial + 0) * self.height_line)) + self.space,
            valor_documento
        )

        self.pdf_canvas.setFont('Courier', 9)
        demonstrativo = boleto_dados.demonstrativo[0:25]
        for i in range(len(demonstrativo)):
            self.pdf_canvas.drawString(
                2 * self.space,
                (-3 * cm + ((linha_inicial + 0) * self.height_line)) -
                (i * heigh_font),
                demonstrativo[i])

        self.pdf_canvas.setFont('Helvetica', 9)

        self.pdf_canvas.restoreState()

        return (self.width, ((linha_inicial + 3) * self.height_line))

    def _drawHorizontalCorteLine(self, x, y, width):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        self.pdf_canvas.setLineWidth(1)
        self.pdf_canvas.setDash(1, 2)
        self.__horizontalLine(0, 0, width)

        self.pdf_canvas.restoreState()

    def _drawVerticalCorteLine(self, x, y, height):
        self.pdf_canvas.saveState()
        self.pdf_canvas.translate(x, y)

        self.pdf_canvas.setLineWidth(1)
        self.pdf_canvas.setDash(1, 2)
        self.__verticalLine(0, 0, height)

        self.pdf_canvas.restoreState()

    def _drawReciboCaixa(self, boleto_dados, x, y):
        """Imprime o Recibo do Caixa

        :param boleto_dados: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boleto_dados: :class:`pyboleto.data.BoletoData`

        """
        self.pdf_canvas.saveState()

        self.pdf_canvas.translate(x, y)

        right_space = 25 if self.carne else 45

        # De baixo para cima posicao 0,0 esta no canto inferior esquerdo
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        y = 1.5 * self.height_line
        self.pdf_canvas.drawRightString(
            self.width,
            (1.5 * self.height_line) + self.delta_title - 1,
            'Autenticação Mecânica / Ficha de Compensação'
        )

        # Primeira linha depois do codigo de barra
        y += self.height_line
        self.pdf_canvas.setLineWidth(2)
        self.__horizontalLine(0, y, self.width)
        # self.pdf_canvas.drawString(
        #     self.width - (45 * mm) + self.space,
        #     y + self.space, 'Código de baixa'
        # )

        self.pdf_canvas.drawString(0, y + self.space, 'Sacador / Avalista:')
        if boleto_dados.sacador_nome:
            sacador = boleto_dados.sacador_nome
            sacador += f' - {boleto_dados.sacador_documento}' if boleto_dados.sacador_documento is not None else ''
            self.pdf_canvas.drawString(16 * mm,  y + self.space, sacador)

        y += self.height_line
        self.pdf_canvas.drawString(0, y + self.delta_title, 'Pagador')
        sacado = boleto_dados.sacado

        # Linha grossa dividindo o Sacado
        y += self.height_line
        self.pdf_canvas.setLineWidth(2)
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        for i in range(len(sacado)):
            self.pdf_canvas.drawString(
                16 * mm,
                (y - 8) - (i * self.delta_font),
                sacado[i]
            )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha vertical limitando todos os campos da direita
        self.pdf_canvas.setLineWidth(1)
        self.__verticalLine(self.width - (right_space * mm), y, 9.5 * self.height_line)
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(=) Valor cobrado'
        )

        # Campos da direita
        y += self.height_line
        self.__horizontalLine(self.width - (right_space * mm), y, right_space * mm)
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(+) Outros acréscimos'
        )

        y += self.height_line
        self.__horizontalLine(self.width - (right_space * mm), y, right_space * mm)
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(+) Mora/Multa'
        )

        y += self.height_line
        self.__horizontalLine(self.width - (right_space * mm), y, right_space * mm)
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(-) Outras deduções'
        )

        y += self.height_line
        self.__horizontalLine(self.width - (right_space * mm), y, right_space * mm)
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(-) Descontos/Abatimentos'
        )
        self.pdf_canvas.drawString(
            0,
            y + self.delta_title,
            'Instruções'
        )

        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        instrucoes = boleto_dados.instrucoes
        for i in range(len(instrucoes)):
            self.pdf_canvas.drawString(
                2 * self.space,
                y - (i * self.delta_font),
                instrucoes[i]
            )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha horizontal com primeiro campo Uso do Banco
        y += self.height_line
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.drawString(0, y + self.delta_title, 'Uso do banco')

        self.__verticalLine((30) * mm, y, 2 * self.height_line)
        self.pdf_canvas.drawString(
            (30 * mm) + self.space,
            y + self.delta_title,
            'Carteira'
        )

        self.__verticalLine((30 + 20) * mm, y, self.height_line)
        self.pdf_canvas.drawString(
            ((30 + 20) * mm) + self.space,
            y + self.delta_title,
            'Espécie'
        )

        self.__verticalLine(
            (30 + 20 + 20) * mm,
            y,
            2 * self.height_line
        )
        self.pdf_canvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.delta_title,
            'Quantidade'
        )

        self.__verticalLine(
            (30 + 20 + 20 + 20 + 20) * mm, y, 2 * self.height_line)
        self.pdf_canvas.drawString(
            ((30 + 40 + 40) * mm) + self.space, y + self.delta_title, 'Valor')

        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            '(=) Valor documento'
        )

        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        self.pdf_canvas.drawString(
            (30 * mm) + self.space,
            y + self.space,
            boleto_dados.carteira
        )
        self.pdf_canvas.drawString(
            ((30 + 20) * mm) + self.space,
            y + self.space,
            boleto_dados.especie
        )
        self.pdf_canvas.drawString(
            ((30 + 20 + 20) * mm) + self.space,
            y + self.space,
            boleto_dados.quantidade
        )
        valor = ''
        if boleto_dados.valor != '0.00':
            valor = self._formataValorParaExibir(boleto_dados.valor)
        self.pdf_canvas.drawString(
            ((30 + 20 + 20 + 20 + 20) * mm) + self.space,
            y + self.space,
            valor
        )
        valor_documento = self._formataValorParaExibir(
            boleto_dados.valor_documento
        )
        self.pdf_canvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            valor_documento
        )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha horizontal com primeiro campo Data documento
        y += self.height_line
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.drawString(
            0,
            y + self.delta_title,
            'Data do documento'
        )
        self.pdf_canvas.drawString(
            (30 * mm) + self.space,
            y + self.delta_title,
            'N. do documento'
        )
        self.pdf_canvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.delta_title,
            'Espécie doc'
        )
        self.__verticalLine(
            (30 + 20 + 20 + 20) * mm,
            y,
            self.height_line
        )
        self.pdf_canvas.drawString(
            ((30 + 40 + 20) * mm) + self.space,
            y + self.delta_title,
            'Aceite'
        )
        self.pdf_canvas.drawString(
            ((30 + 40 + 40) * mm) + self.space,
            y + self.delta_title,
            'Data processamento'
        )
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            'Nosso número'
        )

        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        self.pdf_canvas.drawString(
            0,
            y + self.space,
            boleto_dados.data_documento.strftime('%d/%m/%Y')
        )
        self.pdf_canvas.drawString(
            (30 * mm) + self.space,
            y + self.space,
            boleto_dados.numero_documento
        )
        self.pdf_canvas.drawString(
            ((30 + 40) * mm) + self.space,
            y + self.space,
            boleto_dados.especie_documento
        )
        self.pdf_canvas.drawString(
            ((30 + 40 + 20) * mm) + self.space,
            y + self.space,
            boleto_dados.aceite
        )
        self.pdf_canvas.drawString(
            ((30 + 40 + 40) * mm) + self.space,
            y + self.space,
            boleto_dados.data_processamento.strftime('%d/%m/%Y')
        )
        self.pdf_canvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boleto_dados.format_nosso_numero()
        )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha horizontal com primeiro campo Cedente
        y += self.height_line
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.drawString(0, y + self.delta_title + 10,
                                   'Beneficiário')
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title + 10,
            boleto_dados.label_cedente
        )

        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        beneficiario = u'{} - {}: {}'.format(
            boleto_dados.cedente,
            doc_label(boleto_dados.cedente_documento),
            boleto_dados.cedente_documento)
        self.pdf_canvas.drawString(0, y + self.space + 10, beneficiario)
        self.pdf_canvas.drawString(0, y + self.space,
                                   boleto_dados.cedente_endereco)
        self.pdf_canvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boleto_dados.agencia_conta_cedente
        )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha horizontal com primeiro campo Local de Pagamento
        y += self.height_line + 10
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.drawString(
            0,
            y + self.delta_title,
            'Local de pagamento'
        )
        self.pdf_canvas.drawString(
            self.width - (right_space * mm) + self.space,
            y + self.delta_title,
            'Vencimento'
        )

        self.pdf_canvas.setFont('Helvetica', self.font_size_value)
        self.pdf_canvas.drawString(
            0,
            y + self.space,
            boleto_dados.local_pagamento
        )
        self.pdf_canvas.drawRightString(
            self.width - 2 * self.space,
            y + self.space,
            boleto_dados.data_vencimento.strftime('%d/%m/%Y')
        )
        self.pdf_canvas.setFont('Helvetica', self.font_size_title)

        # Linha grossa com primeiro campo logo tipo do banco
        self.pdf_canvas.setLineWidth(2)
        y += self.height_line
        self.__horizontalLine(0, y, self.width)
        self.pdf_canvas.setLineWidth(2)
        self.__verticalLine(25.5 * mm if self.carne else 40 * mm, y, self.height_line)  # Logo Tipo
        self.__verticalLine(39 * mm if self.carne else 60 * mm, y, self.height_line)  # Numero do Banco

        if boleto_dados.logo_image:
            logo_image_path = load_image(boleto_dados.logo_image)
            self.pdf_canvas.drawImage(
                logo_image_path,
                0,
                y + self.space + 1,
                40 * mm,
                self.height_line,
                preserveAspectRatio=True,
                anchor='sw'
            )
        self.pdf_canvas.setFont('Helvetica-Bold', 12)
        self.pdf_canvas.drawCentredString(
            32 * mm if self.carne else 50 * mm,
            y + 2 * self.space,
            boleto_dados.codigo_dv_banco
        )
        self.pdf_canvas.setFont('Helvetica-Bold', 11.5)
        self.pdf_canvas.drawRightString(
            self.width,
            y + 2 * self.space,
            boleto_dados.linha_digitavel
        )

        # Codigo de barras
        self._codigoBarraI25(boleto_dados.barcode, 7 * self.space, 0)

        self.pdf_canvas.restoreState()

        return self.width, (y + self.height_line)

    def drawBoletoCarne(self, boletoDados1, boletoDados2=None, boletoDados3=None):
        """Imprime um boleto tipo carnê com 3 boletos por página.

        :param boletoDados1: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :param boletoDados2: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :param boletoDados3: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boletoDados1: :class:`pyboleto.data.BoletoData`
        :type boletoDados2: :class:`pyboleto.data.BoletoData`
        :type boletoDados3: :class:`pyboleto.data.BoletoData`

        """
        x = 5 * mm
        y = 10 * mm
        d = self._drawBoletoCarne(boletoDados1, y)
        y += d[1] + 3 * mm

        # Linha inferior
        self._drawHorizontalCorteLine(x, 6 * mm, d[0] - x)

        # Linha Superior
        self._drawHorizontalCorteLine(x, y, d[0] - x)

        if boletoDados2:
            y += 4 * mm
            d = self._drawBoletoCarne(boletoDados2, y)
            y += d[1] + 3 * mm

            # Linha Superior
            self._drawHorizontalCorteLine(x, y, d[0] - x)

        if boletoDados3:
            y += 4 * mm
            d = self._drawBoletoCarne(boletoDados3, y)
            y += d[1] + 3 * mm

            # Linha Superior
            self._drawHorizontalCorteLine(x, y, d[0] - x)

    def _drawBoletoCarne(self, boleto_dados, y):
        """Imprime apenas dos boletos do carnê.

        :param boleto_dados: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boleto_dados: :class:`pyboleto.data.BoletoData`
        """
        x = 5 * mm if self.carne else 15 * mm
        d = self._draw_recibo_sacado_canhoto(boleto_dados, x, y)
        x += d[0] + 1 * mm
        self._drawVerticalCorteLine(x, y, d[1])
        x += 1 * mm
        d = self._drawReciboCaixa(boleto_dados, x, y)
        x += d[0]
        return x, d[1]

    def drawBoleto(self, boleto_dados):
        """Imprime Boleto Convencional

        Você pode chamar este método diversas vezes para criar um arquivo com
        várias páginas, uma por boleto.

        :param boleto_dados: Objeto com os dados do boleto a ser preenchido.
            Deve ser subclasse de :class:`pyboleto.data.BoletoData`
        :type boleto_dados: :class:`pyboleto.data.BoletoData`
        """
        x = 9 * mm  # margem esquerda
        y = 14 * mm  # margem inferior

        # self._drawHorizontalCorteLine(x, y, self.width)
        # y += 4 * mm  # distancia entre linha de corte e barcode

        d = self._drawReciboCaixa(boleto_dados, x, y)
        y += d[1] + (12 * mm)  # distancia entre Recibo caixa e linha de corte

        self._drawHorizontalCorteLine(x, y, self.width)

        y += 20 * mm
        d = self._drawReciboSacado(boleto_dados, x, y)
        y += d[1]
        return (self.width, y)

    def nextPage(self):
        """Força início de nova página"""

        self.pdf_canvas.showPage()

    def save(self):
        """Fecha boleto e constroi o arquivo"""

        self.pdf_canvas.save()

    def __horizontalLine(self, x, y, width):
        self.pdf_canvas.line(x, y, x + width, y)

    def __verticalLine(self, x, y, width):
        self.pdf_canvas.line(x, y, x, y + width)

    def _formataValorParaExibir(self, nfloat):
        if nfloat:
            txt = nfloat
            txt = txt.replace('.', ',')
        else:
            txt = ""
        return txt

    def _codigoBarraI25(self, num, x, y):
        """Imprime Código de barras otimizado para boletos

        O código de barras é otmizado para que o comprimeto seja sempre o
        estipulado pela febraban de 103mm.

        """
        # http://en.wikipedia.org/wiki/Interleaved_2_of_5

        altura = 13 * mm
        comprimento = 103 * mm

        thin_bar = 0.254320987654 * mm  # Tamanho correto aproximado

        bc = I2of5(num,
                   barWidth=thin_bar,
                   ratio=3,
                   barHeight=altura,
                   bearers=0,
                   quiet=0,
                   checksum=0)

        # Recalcula o tamanho do thin_bar para que o cod de barras tenha o
        # comprimento correto
        thin_bar = (thin_bar * comprimento) / bc.width
        bc.__init__(num, barWidth=thin_bar)

        bc.drawOn(self.pdf_canvas, x, y)


def load_image(logo_image):
    """Load Bank Image"""
    pyboleto_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(pyboleto_dir, 'media', logo_image)
    return image_path
