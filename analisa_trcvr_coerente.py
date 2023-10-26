def fwhm(dicio, DEBUG=False):
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    header = dicio['cabecalhos']

    df = dicio['tabela']
    df.groupby(header['Payload']).head(2)
    
    if DEBUG: display(df.style.set_caption(dicio['fabricante'] + dicio['PN'] + ' ' + dicio['descricao'])# + ': ' + dicio['cotacao'])
            )
    
    # se não existe a info FWHM
    if not header['FWHM'] in df.columns:
        # mas existe a info GBaud
        if header['GBaud'] in df.columns: 
            # cria a largura de banda (spectrum width) a partir de GBaud
            df["FWHM [GHz]"] = df['GBaud'] # FWHM, supondo que pra esse modulo, GBaud = FWHM

    # se existe a info FWHM
    if header['FWHM'] in df.columns:
        # Flexgrid ch width
        df["FlexGrid Ch Width [GHz]"] = (np.ceil(df.loc[:,'GBaud']/12.5)*12.5).round(2)
        # Spectrum efficiency = net bit rate / symbol rate
        df['Spectrum Efficiency [bits/s/Hz]'] = df['Line Rate [Gbps]']/df["FWHM [GHz]"]
        df.groupby('Line Rate [Gbps]').head(2)
        df.style.set_caption(dicio['fabricante'] + dicio['PN'] + ' ' + dicio['descricao'])# + ': ' + dicio['cotacao'])
        # Custo x SE
        df['USD/SE'] = dicio['custo']/df['Spectrum Efficiency [bits/s/Hz]']

        #### Plota EFICIENCIA ESPECTRAL x OSNR #######
        plt.rc('font', size=15)
        plt.rc('lines', linewidth=3)
        #plt.rc('markersize',markersize=3)
        fig, axs = plt.subplots(1,1, figsize=(8, 5))

        pol, residuo = np.polynomial.polynomial.Polynomial.fit(df["OSNR Sensitivity [dB/0.1nm]"],df['Spectrum Efficiency [bits/s/Hz]'],2,full=True)
        t = np.linspace(min(df['OSNR Sensitivity [dB/0.1nm]'].iloc[:]),max(df['OSNR Sensitivity [dB/0.1nm]'].iloc[:]),200)
        df.plot.scatter(ax=axs,x="OSNR Sensitivity [dB/0.1nm]",y="Spectrum Efficiency [bits/s/Hz]",alpha=0.7, marker='.', label=dicio['fabricante']+' '+dicio['FF']+' '+dicio['PN'])
        plt.plot(t,pol(t),'-')

        plt.title('Spectral Efficiency for ' + dicio['descricao'])
        plt.xlabel("EOL Rx OSNR [dB/0.1nm]")
        plt.ylabel("Spectrum Efficiency [bits/s/Hz]")

        if DEBUG: print('Residuo do ajuste: ', residuo[1])


        ##### Plota Custo por ES x OSNR ############
        plt.rc('font', size=15)
        plt.rc('lines', linewidth=3)
        #plt.rc('markersize',markersize=3)
        fig, axs = plt.subplots(figsize=(8, 5))

        pol, residuo = np.polynomial.polynomial.Polynomial.fit(df[header['ROSNR1']],df['USD/SE'],2,full=True)
        t = np.linspace(min(df[header['ROSNR1']].iloc[:]),max(df[header['ROSNR1']].iloc[:]),200)
        df.plot.scatter(ax=axs,x=header['ROSNR1'],y="USD/SE",alpha=0.7, marker='.', label=dicio['fabricante']+' '+dicio['FF']+' '+dicio['PN'])
        plt.plot(t,pol(t),'-')

        plt.title('Preços FOB 2023 para 1000pcs')
        plt.xlabel("EOL Rx OSNR [dB/0.1nm]")
        plt.ylabel("Cost x Spectrum Efficiency [USD/bits/s/Hz]")
        plt.show()


    
    return df # df =  tabela com dados incluindo FWHM e SE.


def custoXbit(dicio, DEBUG=False):
    import pandas as pd
    import matplotlib.pyplot as plt
    import numpy as np

    header = dicio['cabecalhos']

    df = dicio['tabela']
    df.groupby(header['Payload']).head(2)
    
    if DEBUG: display(df.style.set_caption(dicio['fabricante'] + dicio['PN'] + ' ' + dicio['descricao'])# + ': ' + dicio['cotacao'])
            )
    
        ## USD/100Gbps Analysis
    if dicio['custo'] > 1e3 :
        # inclui a coluna USD/100Gbps
        df['USD/100Gbps'] = dicio["custo"]/(df[header['Payload']]/100)

        ###### Custo x bit em degraus ############
        # organiza por OSNR e depois elimina aqueles que tem a mesma taxa Gbps e USD/bit
        custoXbit = df.sort_values(by=header['ROSNR1']).drop_duplicates(subset=[header['Payload'],'USD/100Gbps'])
        #duplica cada linha
        custoXbit = pd.concat([custoXbit]*2).sort_values(by=header['Payload'],ignore_index=True)
        for k in range(1,len(custoXbit)-1):
            # usa o valor de OSNR da seguinte linha para criar o degrau
            custoXbit.loc[k,header['ROSNR1']]=custoXbit.loc[k+1,header['ROSNR1']]
        # adiciona o ultimo degrau
        df = pd.DataFrame(custoXbit[-1:])
        custoXbit = pd.concat([custoXbit,df],ignore_index=True)
        custoXbit.loc[custoXbit.index[-1],header['ROSNR1']] = custoXbit.loc[custoXbit.index[-1],header['ROSNR1']]+1
        # imprime
        print('Tabela Custo x Bit:')
        display(custoXbit.style.set_caption(dicio['fabricante'] +dicio['PN']+' ,' + dicio['descricao'] + ', ' + ' ' + dicio['cotacao']))

        # Plota custo x bit
        fig, axs = plt.subplots(figsize=(8, 5))
        #
        df = custoXbit[[header['Payload'],header['ROSNR1'],'USD/100Gbps']].dropna()
        df.plot(ax=axs,x=header['ROSNR1'],y='USD/100Gbps',alpha=0.7,label=(dicio['fabricante']+' '+dicio['FF']+' '+dicio['PN']))
        for k in range(1, len(df), 2):
            plt.text(df.iloc[k,1],df.iloc[k,2],df.iloc[k,0])
            
        plt.xlabel("EOL Rx OSNR[dB/0.1nm]")
        plt.ylabel("Custo x Bit, USD/100Gbps")
        plt.title(dicio['fabricante'] +' ' +dicio['PN'] +', ' +dicio['descricao'])# + dicio['cotacao']) 
        print(dicio['cotacao'])

        return df # df = custo x bit em degraus.
    else:
        print('ERRO: Incoerencia no custo do módulo.')
    
