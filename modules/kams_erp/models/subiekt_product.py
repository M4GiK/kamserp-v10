# -*- coding: utf-8 -*-
# @COPYRIGHT_begin
#
# Copyright [2016] Michał Szczygieł (m4gik), M4GiK Software
#
# @COPYRIGHT_end
from sqlalchemy import BINARY, Column, ForeignKey, Integer, String, Text, text, Index, DateTime, LargeBinary, \
    SmallInteger, desc
from sqlalchemy.dialects.mssql.base import BIT, MONEY
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class TwTowar(Base):
    __tablename__ = u'tw__Towar'

    tw_Id = Column(Integer, primary_key=True)
    tw_Zablokowany = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_Rodzaj = Column(Integer, nullable=False, server_default=text("((1))"))
    tw_Symbol = Column(String(20, u'Polish_CI_AS'), nullable=False)
    tw_Nazwa = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Opis = Column(String(255, u'Polish_CI_AS'), nullable=False)
    tw_IdVatSp = Column(ForeignKey(u'sl_StawkaVAT.vat_Id'))
    tw_IdVatZak = Column(ForeignKey(u'sl_StawkaVAT.vat_Id'))
    tw_JakPrzySp = Column(BIT, nullable=False, server_default=text("((1))"))
    tw_JednMiary = Column(String(10, u'Polish_CI_AS'), nullable=False)
    tw_PKWiU = Column(String(20, u'Polish_CI_AS'), nullable=False)
    tw_SWW = Column(String(20, u'Polish_CI_AS'), nullable=False)
    tw_IdRabat = Column(ForeignKey(u'sl_Rabat.rt_id'))
    tw_IdOpakowanie = Column(ForeignKey(u'tw__Towar.tw_Id'))
    tw_PrzezWartosc = Column(BIT, nullable=False, server_default=text("((1))"))
    tw_IdPodstDostawca = Column(ForeignKey(u'kh__Kontrahent.kh_Id'))
    tw_DostSymbol = Column(String(20, u'Polish_CI_AS'), nullable=False)
    tw_CzasDostawy = Column(Integer)
    tw_UrzNazwa = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_PLU = Column(Integer)
    tw_PodstKodKresk = Column(String(20, u'Polish_CI_AS'), nullable=False)
    tw_IdTypKodu = Column(Integer)
    tw_CenaOtwarta = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_WagaEtykiet = Column(BIT, server_default=text("((0))"))
    tw_KontrolaTW = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_StanMin = Column(MONEY)
    tw_JednStanMin = Column(String(10, u'Polish_CI_AS'))
    tw_DniWaznosc = Column(Integer)
    tw_IdGrupa = Column(ForeignKey(u'sl_GrupaTw.grt_Id'))
    tw_WWW = Column(String(255, u'Polish_CI_AS'), nullable=False)
    tw_SklepInternet = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_Pole1 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole2 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole3 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole4 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole5 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole6 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole7 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Pole8 = Column(String(50, u'Polish_CI_AS'), nullable=False)
    tw_Uwagi = Column(String(255, u'Polish_CI_AS'), nullable=False)
    tw_Logo = Column(BINARY(50))
    tw_Usuniety = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_Objetosc = Column(MONEY)
    tw_Masa = Column(MONEY)
    tw_Charakter = Column(Text(collation=u'Polish_CI_AS'))
    tw_JednMiaryZak = Column(String(10, u'Polish_CI_AS'), nullable=False)
    tw_JMZakInna = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_KodTowaru = Column(String(8, u'Polish_CI_AS'))
    tw_IdKrajuPochodzenia = Column(ForeignKey(u'sl_KrajPochodzenia.krp_Id'))
    tw_IdUJM = Column(Integer)
    tw_JednMiarySprz = Column(String(10, u'Polish_CI_AS'), nullable=False)
    tw_JMSprzInna = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_SerwisAukcyjny = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_IdProducenta = Column(ForeignKey(u'kh__Kontrahent.kh_Id'))
    tw_SprzedazMobilna = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_IsFundPromocji = Column(BIT)
    tw_IdFundPromocji = Column(Integer)
    tw_DomyslnaKategoria = Column(Integer)
    tw_Wysokosc = Column(MONEY)
    tw_Szerokosc = Column(MONEY)
    tw_Glebokosc = Column(MONEY)
    tw_StanMaks = Column(MONEY)
    tw_Akcyza = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_AkcyzaZaznacz = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_AkcyzaKwota = Column(MONEY)
    tw_ObrotMarza = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_OdwrotneObciazenie = Column(BIT, nullable=False, server_default=text("((0))"))
    tw_ProgKwotowyOO = Column(Integer, nullable=False, server_default=text("((0))"))
    tw_DodawalnyDoZW = Column(BIT, nullable=False, server_default=text("((0))"))

    # sl_GrupaTw = relationship(u'SlGrupaTw')
    # sl_KrajPochodzenia = relationship(u'SlKrajPochodzenia')
    parent = relationship(u'TwTowar', remote_side=[tw_Id])
    # kh__Kontrahent = relationship(u'KhKontrahent', primaryjoin='TwTowar.tw_IdPodstDostawca == KhKontrahent.kh_Id')
    # kh__Kontrahent1 = relationship(u'KhKontrahent', primaryjoin='TwTowar.tw_IdProducenta == KhKontrahent.kh_Id')
    # sl_Rabat = relationship(u'SlRabat')
    # sl_StawkaVAT = relationship(u'SlStawkaVAT', primaryjoin='TwTowar.tw_IdVatSp == SlStawkaVAT.vat_Id')
    # sl_StawkaVAT1 = relationship(u'SlStawkaVAT', primaryjoin='TwTowar.tw_IdVatZak == SlStawkaVAT.vat_Id')


class TwStan(Base):
    __tablename__ = u'tw_Stan'
    __table_args__ = (
        Index(u'IX_tw_Stany', u'st_TowId', u'st_MagId', unique=True),
        Index(u'IX_tw_Stany_1', u'st_TowId', u'st_MagId', u'st_Stan', u'st_StanRez')
    )

    st_TowId = Column(ForeignKey(u'tw__Towar.tw_Id'), primary_key=True, nullable=False)
    st_MagId = Column(ForeignKey(u'sl_Magazyn.mag_Id'), primary_key=True, nullable=False)
    st_Stan = Column(MONEY, nullable=False)
    st_StanMin = Column(MONEY, nullable=False)
    st_StanRez = Column(MONEY, nullable=False)
    st_StanMax = Column(MONEY, nullable=False, server_default=text("((0))"))

    # sl_Magazyn = relationship(u'SlMagazyn')
    tw__Towar = relationship(u'TwTowar')


class TwCena(Base):
    __tablename__ = u'tw_Cena'

    tc_Id = Column(Integer, primary_key=True)
    tc_IdTowar = Column(ForeignKey(u'tw__Towar.tw_Id'), nullable=False, unique=True)
    tc_CenaNetto0 = Column(MONEY)
    tc_CenaBrutto0 = Column(MONEY)
    tc_WalutaId = Column(String(3, u'Polish_CI_AS'))
    tc_IdWalutaKurs = Column(Integer)
    tc_WalutaKurs = Column(MONEY)
    tc_CenaNettoWaluta = Column(MONEY)
    tc_CenaNettoWaluta2 = Column(MONEY)
    tc_CenaWalutaNarzut = Column(MONEY)
    tc_WalutaJedn = Column(String(10, u'Polish_CI_AS'), nullable=False)
    tc_PodstawaKC = Column(Integer, server_default=text("((0))"))
    tc_CenaNetto1 = Column(MONEY)
    tc_CenaNetto2 = Column(MONEY)
    tc_CenaNetto3 = Column(MONEY)
    tc_CenaNetto4 = Column(MONEY)
    tc_CenaNetto5 = Column(MONEY)
    tc_CenaNetto6 = Column(MONEY)
    tc_CenaNetto7 = Column(MONEY)
    tc_CenaNetto8 = Column(MONEY)
    tc_CenaNetto9 = Column(MONEY)
    tc_CenaNetto10 = Column(MONEY)
    tc_CenaBrutto1 = Column(MONEY)
    tc_CenaBrutto2 = Column(MONEY)
    tc_CenaBrutto3 = Column(MONEY)
    tc_CenaBrutto4 = Column(MONEY)
    tc_CenaBrutto5 = Column(MONEY)
    tc_CenaBrutto6 = Column(MONEY)
    tc_CenaBrutto7 = Column(MONEY)
    tc_CenaBrutto8 = Column(MONEY)
    tc_CenaBrutto9 = Column(MONEY)
    tc_CenaBrutto10 = Column(MONEY)
    tc_Zysk1 = Column(MONEY)
    tc_Zysk2 = Column(MONEY)
    tc_Zysk3 = Column(MONEY)
    tc_Zysk4 = Column(MONEY)
    tc_Zysk5 = Column(MONEY)
    tc_Zysk6 = Column(MONEY)
    tc_Zysk7 = Column(MONEY)
    tc_Zysk8 = Column(MONEY)
    tc_Zysk9 = Column(MONEY)
    tc_Zysk10 = Column(MONEY)
    tc_Narzut1 = Column(MONEY)
    tc_Narzut2 = Column(MONEY)
    tc_Narzut3 = Column(MONEY)
    tc_Narzut4 = Column(MONEY)
    tc_Narzut5 = Column(MONEY)
    tc_Narzut6 = Column(MONEY)
    tc_Narzut7 = Column(MONEY)
    tc_Narzut8 = Column(MONEY)
    tc_Narzut9 = Column(MONEY)
    tc_Narzut10 = Column(MONEY)
    tc_Marza1 = Column(MONEY)
    tc_Marza2 = Column(MONEY)
    tc_Marza3 = Column(MONEY)
    tc_Marza4 = Column(MONEY)
    tc_Marza5 = Column(MONEY)
    tc_Marza6 = Column(MONEY)
    tc_Marza7 = Column(MONEY)
    tc_Marza8 = Column(MONEY)
    tc_Marza9 = Column(MONEY)
    tc_Marza10 = Column(MONEY)
    tc_IdWaluta0 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta1 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta2 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta3 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta4 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta5 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta6 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta7 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta8 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta9 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_IdWaluta10 = Column(String(3, u'Polish_CI_AS'), nullable=False, server_default=text("('PLN')"))
    tc_KursWaluty1 = Column(Integer)
    tc_KursWaluty2 = Column(Integer)
    tc_KursWaluty3 = Column(Integer)
    tc_KursWaluty4 = Column(Integer)
    tc_KursWaluty5 = Column(Integer)
    tc_KursWaluty6 = Column(Integer)
    tc_KursWaluty7 = Column(Integer)
    tc_KursWaluty8 = Column(Integer)
    tc_KursWaluty9 = Column(Integer)
    tc_KursWaluty10 = Column(Integer)
    tc_DataKursuWaluty = Column(DateTime)
    tc_BankKursuWaluty = Column(Integer)

    tw__Towar = relationship(u'TwTowar')


class TwDokument(Base):
    __tablename__ = u'tw_Dokument'

    tdk_Id = Column(Integer, primary_key=True)
    tdk_IdTowaru = Column(ForeignKey(u'tw__Towar.tw_Id'), nullable=False)
    tdk_IdKategorii = Column(ForeignKey(u'sl_KategoriaDokumentu.kd_Id'), nullable=False)
    tdk_Zablokowany = Column(BIT, nullable=False)
    tdk_DataModyfikacji = Column(DateTime, nullable=False)
    tdk_Nazwa = Column(String(255, u'Polish_CI_AS'), nullable=False)
    tdk_Opis = Column(String(255, u'Polish_CI_AS'), nullable=False)
    tdk_Tresc = Column(LargeBinary, nullable=False)
    tdk_Typ = Column(String(1000, u'Polish_CI_AS'), nullable=False)
    tdk_IdPersonelu = Column(ForeignKey(u'pd_Uzytkownik.uz_Id'), nullable=False)

    # sl_KategoriaDokumentu = relationship(u'SlKategoriaDokumentu')
    # pd_Uzytkownik = relationship(u'PdUzytkownik')
    tw__Towar = relationship(u'TwTowar')


class TwNarzutTw(Base):
    __tablename__ = u'tw_NarzutTw'
    __table_args__ = (
        Index(u'IX_tw_NarzutTw', u'ct_IdCena', u'ct_IdNarzut', u'ct_Kolejnosc', unique=True),
    )

    ct_Id = Column(Integer, primary_key=True)
    ct_IdCena = Column(ForeignKey(u'tw_Cena.tc_Id'), nullable=False)
    ct_IdNarzut = Column(Integer, nullable=False)
    ct_Kolejnosc = Column(Integer, nullable=False)
    ct_Narzut = Column(MONEY)
    ct_Wartosc = Column(MONEY)

    tw_Cena = relationship(u'TwCena')


class DokDokument(Base):
    __tablename__ = u'dok__Dokument'
    __table_args__ = (
        Index(u'IX_dok__Dokument_5', u'dok_Id', u'dok_NrPelny', u'dok_DoDokNrPelny', u'dok_OdbiorcaAdreshId'),
        Index(u'IX_dok__Dokument_2', u'dok_Typ', u'dok_MagId', u'dok_Nr', u'dok_NrRoz', u'dok_DataWyst'),
        Index(u'IX_dok__Dokument', u'dok_DoDokId', u'dok_Typ', u'dok_Podtyp'),
        Index(u'IX_dok__Dokument_4', u'dok_Typ', u'dok_Podtyp', u'dok_NrPelnyOryg', u'dok_PlatnikId')
    )

    dok_Id = Column(Integer, primary_key=True)
    dok_Typ = Column(Integer, nullable=False)
    dok_Podtyp = Column(Integer, nullable=False)
    dok_MagId = Column(Integer)
    dok_Nr = Column(Integer)
    dok_NrRoz = Column(String(3, u'Polish_CI_AS'))
    dok_NrPelny = Column(String(30, u'Polish_CI_AS'), nullable=False)
    dok_NrPelnyOryg = Column(String(30, u'Polish_CI_AS'), nullable=False)
    dok_DoDokId = Column(Integer)
    dok_DoDokNrPelny = Column(String(30, u'Polish_CI_AS'), nullable=False)
    dok_DoDokDataWyst = Column(DateTime)
    dok_MscWyst = Column(String(40, u'Polish_CI_AS'), nullable=False)
    dok_DataWyst = Column(DateTime, nullable=False, index=True)
    dok_DataMag = Column(DateTime, nullable=False)
    dok_DataOtrzym = Column(DateTime, index=True)
    dok_PlatnikId = Column(Integer)
    dok_PlatnikAdreshId = Column(Integer)
    dok_OdbiorcaId = Column(Integer)
    dok_OdbiorcaAdreshId = Column(Integer)
    dok_PlatId = Column(Integer)
    dok_PlatTermin = Column(DateTime)
    dok_Wystawil = Column(String(40, u'Polish_CI_AS'), nullable=False)
    dok_Odebral = Column(String(40, u'Polish_CI_AS'), nullable=False)
    dok_PersonelId = Column(Integer)
    dok_CenyPoziom = Column(Integer)
    dok_CenyTyp = Column(Integer)
    dok_CenyKurs = Column(MONEY)
    dok_CenyNarzut = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_RabatProc = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartUsNetto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartUsBrutto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartTwNetto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartTwBrutto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartOpZwr = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartOpWyd = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartMag = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartMagP = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartMagR = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartNetto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartVat = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_WartBrutto = Column(MONEY, nullable=False, server_default=text("((0))"))
    dok_KwWartosc = Column(MONEY, server_default=text("((0))"))
    dok_KwGotowka = Column(MONEY)
    dok_KwKarta = Column(MONEY)
    dok_KwDoZaplaty = Column(MONEY)
    dok_KwKredyt = Column(MONEY)
    dok_KwReszta = Column(MONEY)
    dok_Waluta = Column(String(3, u'Polish_CI_AS'))
    dok_WalutaKurs = Column(MONEY, nullable=False, server_default=text("((1))"))
    dok_Uwagi = Column(String(500, u'Polish_CI_AS'), nullable=False)
    # dok_KatId = Column(ForeignKey(u'sl_Kategoria.kat_Id'))
    dok_Tytul = Column(String(50, u'Polish_CI_AS'), nullable=False)
    dok_Podtytul = Column(String(50, u'Polish_CI_AS'), nullable=False)
    dok_Status = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_StatusKsieg = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_StatusFiskal = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_StatusBlok = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_JestTylkoDoOdczytu = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_JestRuchMag = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_JestZmianaDatyDokKas = Column(BIT, nullable=False, server_default=text("((1))"))
    dok_JestHOP = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_JestVatNaEksport = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_JestVatAuto = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_Algorytm = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_KartaId = Column(Integer)
    dok_KredytId = Column(Integer)
    dok_RodzajOperacjiVat = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_KodRodzajuTransakcji = Column(Integer)
    dok_StatusEx = Column(Integer, server_default=text("((0))"))
    dok_ObiektGT = Column(Integer)
    dok_Rozliczony = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_RejId = Column(Integer)
    dok_TerminRealizacji = Column(DateTime)
    dok_WalutaLiczbaJednostek = Column(Integer, nullable=False, server_default=text("((1))"))
    dok_WalutaRodzajKursu = Column(Integer)
    dok_WalutaDataKursu = Column(DateTime)
    dok_WalutaIdBanku = Column(Integer)
    dok_CenyLiczbaJednostek = Column(Integer, nullable=False, server_default=text("((1))"))
    dok_CenyRodzajKursu = Column(Integer)
    dok_CenyDataKursu = Column(DateTime)
    dok_CenyIdBanku = Column(Integer)
    dok_KwPrzelew = Column(MONEY)
    dok_KwGotowkaPrzedplata = Column(MONEY)
    dok_KwPrzelewPrzedplata = Column(MONEY)
    dok_DefiniowalnyId = Column(Integer)
    dok_TransakcjaId = Column(Integer)
    dok_TransakcjaSymbol = Column(String(30, u'Polish_CI_AS'))
    dok_TransakcjaData = Column(DateTime)
    dok_PodsumaVatFSzk = Column(Integer)
    dok_ZlecenieId = Column(Integer)
    dok_NaliczajFundusze = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_PrzetworzonoZKwZD = Column(BIT)
    dok_VatMarza = Column(BIT)
    dok_DstNr = Column(Integer)
    dok_DstNrRoz = Column(String(3, u'Polish_CI_AS'))
    dok_DstNrPelny = Column(String(30, u'Polish_CI_AS'))
    dok_ObslugaDokDost = Column(Integer)
    dok_AkcyzaZwolnienieId = Column(Integer)
    dok_ProceduraMarzy = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_FakturaUproszczona = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_DataZakonczenia = Column(DateTime)
    dok_MetodaKasowa = Column(BIT, nullable=False, server_default=text("((0))"))
    dok_TypNrIdentNabywcy = Column(Integer, nullable=False, server_default=text("((0))"))
    dok_NrIdentNabywcy = Column(String(20, u'Polish_CI_AS'))
    dok_AdresDostawyId = Column(Integer)
    dok_AdresDostawyAdreshId = Column(Integer)
    dok_VenderoId = Column(Integer)
    dok_VenderoSymbol = Column(String(30, u'Polish_CI_AS'))
    dok_VenderoData = Column(DateTime)
    dok_SelloId = Column(Integer)
    dok_SelloSymbol = Column(String(100, u'Polish_CI_AS'))
    dok_SelloData = Column(DateTime)
    dok_TransakcjaJednolitaId = Column(Integer)
    dok_PodpisanoElektronicznie = Column(BIT)
    dok_UwagiExt = Column(String(3500, u'Polish_CI_AS'), nullable=False)
    dok_VenderoStatus = Column(Integer)

    # sl_Kategoria = relationship(u'SlKategoria')


class DokPozycja(Base):
    __tablename__ = u'dok_Pozycja'
    __table_args__ = (
        Index(u'IX_dok_Pozycja_4', u'ob_Id', u'ob_DokHanId', u'ob_DokMagId', u'ob_Ilosc', u'ob_CenaNetto',
              u'ob_CenaBrutto', u'ob_WartNetto', u'ob_WartBrutto'),
    )

    ob_Id = Column(Integer, primary_key=True)
    ob_DoId = Column(ForeignKey(u'dok_Pozycja.ob_Id'), index=True)
    ob_Znak = Column(SmallInteger, nullable=False)
    ob_Status = Column(Integer)
    ob_DokHanId = Column(ForeignKey(u'dok__Dokument.dok_Id'), index=True)
    ob_DokMagId = Column(ForeignKey(u'dok__Dokument.dok_Id'), index=True)
    ob_TowId = Column(ForeignKey(u'tw__Towar.tw_Id'), index=True)
    ob_TowRodzaj = Column(Integer, nullable=False, server_default=text("((1))"))
    ob_Opis = Column(String(255, u'Polish_CI_AS'))
    ob_DokHanLp = Column(Integer)
    ob_DokMagLp = Column(Integer)
    ob_Ilosc = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_IloscMag = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_Jm = Column(String(10, u'Polish_CI_AS'))
    ob_CenaMag = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_CenaWaluta = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_CenaNetto = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_CenaBrutto = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_Rabat = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_WartMag = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_WartNetto = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_WartVat = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_WartBrutto = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_VatId = Column(Integer)
    ob_VatProc = Column(MONEY, nullable=False, server_default=text("((0))"))
    ob_Termin = Column(DateTime)
    ob_MagId = Column(Integer)
    ob_NumerSeryjny = Column(String(40, u'Polish_CI_AS'))
    ob_KategoriaId = Column(Integer)
    ob_Akcyza = Column(BIT)
    ob_AkcyzaKwota = Column(MONEY)
    ob_AkcyzaWartosc = Column(MONEY)
    ob_CenaNabycia = Column(MONEY)
    ob_WartNabycia = Column(MONEY)
    ob_PrzyczynaKorektyId = Column(Integer)

    parent = relationship(u'DokPozycja', remote_side=[ob_Id])
    dok__Dokument = relationship(u'DokDokument', primaryjoin='DokPozycja.ob_DokHanId == DokDokument.dok_Id')
    dok__Dokument1 = relationship(u'DokDokument', primaryjoin='DokPozycja.ob_DokMagId == DokDokument.dok_Id')
    tw__Towar = relationship(u'TwTowar')


def get_last_buy_price(subiekt_session, barcode):
    """
    Gets last buy price.
    :param subiekt_session: session of subiekt database
    :param barcode: product code ean13
    :return: Last buy netto price.
    """
    netto_price = 0.00

    if barcode != '':
        query = subiekt_session.query(TwTowar).filter(TwTowar.tw_PodstKodKresk == barcode)
        towar = query.first()
        if towar:
            document = subiekt_session.query(DokDokument, DokPozycja) \
                .outerjoin(DokPozycja, DokDokument.dok_Id == DokPozycja.ob_DokHanId).filter(DokDokument.dok_Typ == 1) \
                .order_by(desc(DokDokument.dok_DataWyst)).filter(DokPozycja.ob_TowId == towar.tw_Id).first()

            if document is not None:
                netto_price = document[1].ob_CenaNetto

    return netto_price
