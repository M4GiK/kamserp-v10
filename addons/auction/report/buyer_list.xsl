<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:fo="http://www.w3.org/1999/XSL/Format">

	<xsl:template match="/">
		<xsl:apply-templates select="achat-listing"/>
	</xsl:template>

	<xsl:template match="achat-listing">
		<document filename="example.pdf">
			<template pageSize="21cm,29.7cm" leftMargin="2.0cm" rightMargin="2.0cm" topMargin="2.0cm" bottomMargin="2.0cm" title="Bordereau acheteur" author="Generated by Tiny ERP, Fabien Pinckaers" allowSplitting="20">
				<pageTemplate id="first">
					<pageGraphics>
						<drawRightString x="19.0cm" y="26.0cm"><xsl:value-of select="date"/></drawRightString>
					</pageGraphics>
					<frame id="col1" x1="2.0cm" y1="2.5cm" width="17.0cm" height="22.7cm"/>
				</pageTemplate>
			</template>
			
			<stylesheet>
				<paraStyle name="name" fontName="Helvetica-Bold" fontSize="16" alignment="center"/>
				<paraStyle name="cost-name" fontName="Helvetica-BoldOblique" fontSize="10" alignment="RIGHT"/>
				<blockTableStyle id="products">
					 <blockAlignment value="RIGHT" start="2,0" stop="-1,-1"/>
					 <lineStyle kind="LINEBELOW" start="0,0" stop="-1,0"/>
					 <lineStyle kind="LINEABOVE" start="0,-1" stop="-1,-1"/>
					 <blockFont name="Helvetica-BoldOblique" size="11" start="0,0" stop="-1,0"/>
					 <blockValign value="TOP"/>
				</blockTableStyle>
			</stylesheet>

			<story>
				<xsl:apply-templates select="auctions"/>
			</story>
		</document>
	</xsl:template>

	<xsl:template match="auctions">
		<para style="name"><xsl:value-of select="title"/></para>
		<xsl:variable name="colWidths">
			<xsl:choose>
				<xsl:when test="count(//cost-index)=0">1.5cm,7.5cm,1cm,2.2cm,2cm</xsl:when>
				<xsl:otherwise>
					<xsl:text>1.5cm,7.5cm,1cm,2.2cm</xsl:text>
					<xsl:for-each select="//cost-index">
						<xsl:text>,2cm</xsl:text>
					</xsl:for-each>
					<xsl:text>,2cm</xsl:text>
				</xsl:otherwise>
			</xsl:choose>
		</xsl:variable>

		<spacer length="1cm"/>
		
		<blockTable style="products" repeatRows="1"> 
			<xsl:attribute name="colWidths">
				<xsl:value-of select="$colWidths"/>
			</xsl:attribute>
			
			<tr>
				<td t="1">Buyer</td>
				<td/>
				<td t="1">Adj.</td>
				<xsl:for-each select="//cost-index">
					<xsl:sort select="id" data-type="number"/>
					<td><para style="cost-name"><xsl:value-of select="name"/></para></td>
				</xsl:for-each>
				<td><para style="cost-name" t="1">To pay</para></td>
				<td><para style="cost-name" t="1">Already paid</para></td>
			</tr>
			
			<xsl:apply-templates select="buyers">
				<xsl:sort select="login" order="ascending" data-type="number"/>
				<xsl:sort select="name" order="ascending"/>
			</xsl:apply-templates>
			
			<tr>
				<td/>
				<td><para><b t="1">Total:</b></para></td>
				<td><xsl:value-of select="sum(buyers/product/price)"/></td>
				<xsl:for-each select="//cost-index">
					<xsl:sort select="id" data-type="number"/>
					<xsl:variable name="cost_id" select="id"/>
					<td><xsl:value-of select="format-number(sum(//buyers/product/cost[id=$cost_id]/amount), '#,##0.00')"/></td>
				</xsl:for-each>
				<td><xsl:value-of select="sum(buyers/product[payment = '']/price) + sum(buyers/product[payment = '']/cost/amount)"/></td>
				<td><xsl:value-of select="sum(buyers/product[payment !='']/price) + sum(buyers/product[payment !='']/cost/amount)"/></td>
			</tr>
		</blockTable>
	</xsl:template>

	<xsl:template match="buyers">
		<xsl:variable name="buyer_id" select="id"/>
		<tr>
			<td><xsl:value-of select="login"/></td>
			<td><xsl:value-of select="name"/></td>
			<td><xsl:value-of select="sum(product/price)"/></td>
			<xsl:for-each select="//cost-index">
				<xsl:sort select="id" data-type="number"/>
				<xsl:variable name="cost_id" select="id"/>
				<td><xsl:value-of select="sum(//buyers[id=$buyer_id]/product/cost[id=$cost_id]/amount)"/></td>
			</xsl:for-each>
			<td><xsl:value-of select="sum(product[payment = '']/price) + sum(product[payment = '']/cost/amount)"/></td>
			<td><xsl:value-of select="sum(product[payment !='']/price) + sum(product[payment !='']/cost/amount)"/></td>
		</tr>
	</xsl:template>

</xsl:stylesheet>
