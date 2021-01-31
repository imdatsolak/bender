# coding: utf-8
import sys

import matplotlib.pyplot as plot
import pandas as pd
from matplotlib import interactive
from matplotlib.markers import TICKLEFT
from sklearn.manifold import TSNE
import matplotlib.patches as mpatches

reload(sys)
sys.setdefaultencoding("utf-8")
interactive(True)

"""
Word distance visualisation tool
"""


class TopicData:
    def __init__(self):
        self.mainWord = None
        self.supportWords = list()
        self.resultWords = list()

    def __init__(self, mainWord, supportWords, resultWords):
        self.mainWord = mainWord
        self.supportWords = supportWords
        self.resultWords = resultWords


class PlotDataProvider:
    def __init__(self):
        self.model = None

    def __init__(self, word2VecModel):
        self.model = word2VecModel

    def plotDataFor(self, topicItem):
        assert self.model is not None, 'Model is not set'
        assert topicItem is not None, 'Topic is None'

        dataForPlot = None

        if isinstance(topicItem, TopicData):
            vocab = list()
            for itemWord in topicItem.supportWords:
                vocab.append(itemWord)
            for itemWord in topicItem.resultWords:
                if itemWord not in vocab:
                    vocab.append(itemWord)

            modelDimensArr = self.model[vocab]
            dimensions = 2
            tsne = TSNE(n_components=dimensions)
            modelArray = tsne.fit_transform(modelDimensArr)
            dataFrame = pd.DataFrame(modelArray)
            vocabSeries = pd.Series(vocab)
            dataForPlot = pd.concat([dataFrame, vocabSeries], axis=1)
            dataForPlot.columns = ['x', 'y', 'word']

        return dataForPlot


class Plotter:
    def __init__(self):
        self.topicData = None
        self.model = None
        self.colorsIterator = 0
        self.colors = ['#005000', '#530053', '#0000ff', '#000000', '#0095ff', '#ff9500', 'r', 'g', 'y', 'm']

    def __init__(self, topicData, model):
        self.topicData = topicData
        self.model = model
        self.colorsIterator = 0
        self.colors = ['#005000', '#530053', '#0000ff', '#000000', '#0095ff', '#ff9500', 'r', 'g', 'y', 'm']


    def plotDataOn(self, mainSubplot, dotsOnlySubplot, plotData, supportWords):
        itemsColor = self.colors[self.colorsIterator]
        mainWordsMarker = TICKLEFT
        mainWordsMarkerSize = 200

        normalWordMarker = 'o'
        normalWordMarkerSize = 50
        wordDotSize = 10
        for i, title in enumerate(plotData['word']):
            isSupportWord = (title in supportWords)
            marker = mainWordsMarker if isSupportWord else normalWordMarker
            size = mainWordsMarkerSize if isSupportWord else normalWordMarkerSize
            wordMarkerSize = mainWordsMarkerSize if isSupportWord else wordDotSize
            textWeight = 'bold' if isSupportWord else 'normal'
            mainSubplot.scatter(plotData['x'][i], plotData['y'][i], c=itemsColor, marker=marker, s=wordMarkerSize)
            mainSubplot.text(plotData['x'][i], plotData['y'][i], title, size=8, zorder=1, color=itemsColor, weight=textWeight)
            if isSupportWord:
                dotsOnlySubplot.text(plotData['x'][i], plotData['y'][i], title, size=10, zorder=1, color=itemsColor, weight='normal')
            dotsOnlySubplot.scatter(plotData['x'][i], plotData['y'][i], c=itemsColor, marker=marker, s=size)


    def saveFigure(self, path=None, name=None, figure=None):
        if figure is None:
            return

        from time import localtime, strftime
        strTime = strftime("%Y-%m-%d %H:%M:%S", localtime())
        filename = ('WordsMap ' if name is None else name)  + strTime + '.png'

        if path is not None:
            filename = path + '/' + filename

        figure.savefig(filename, bbox_inches='tight')

    def showData(self, separate=False, save = False, outputDir = None, show=True):
        print 'Plot is prepearing'

        sharedFigure = plot.figure(figsize=(25, 13))
        sharedMainSubplot = sharedFigure.add_subplot(2, 1, 1)
        sharedDotsOnlySubplot = sharedFigure.add_subplot(2, 1, 2)

        legendItems = []
        legendTitles = []

        for topicDataItem in self.topicData:
            plotData = PlotDataProvider(self.model).plotDataFor(topicDataItem)
            if plotData is None:
                print 'Will not show plot for ' + topicDataItem.mainWord
                continue

            if separate:
                ''''create figure for each topic'''
                figure = plot.figure(figsize=(25, 13))
                mainSubplot = figure.add_subplot(2, 1, 1)
                dotsOnlySubplot = figure.add_subplot(2, 1, 2)
                self.plotDataOn(mainSubplot=mainSubplot, dotsOnlySubplot=dotsOnlySubplot, plotData=plotData, supportWords=topicDataItem.supportWords)
                figure.legend(handles=[mpatches.Patch(color=self.colors[self.colorsIterator], label=topicDataItem.mainWord)], labels=[topicDataItem.mainWord])

            self.plotDataOn(mainSubplot=sharedMainSubplot, dotsOnlySubplot=sharedDotsOnlySubplot, plotData=plotData, supportWords=topicDataItem.supportWords)
            legendItems.append(mpatches.Patch(color=self.colors[self.colorsIterator], label=topicDataItem.mainWord))
            legendTitles.append(topicDataItem.mainWord)


            '''show and save each plot'''
            if separate:
                if save:
                    self.saveFigure(path=outputDir, name=topicDataItem.mainWord, figure=figure)
                if show:
                    figure.show()

            '''Increase color'''
            self.colorsIterator += 1
            if self.colorsIterator >= len(self.colors):
                self.colorsIterator = 0
        sharedFigure.legend(handles=legendItems, labels=legendTitles)
        if save:
            self.saveFigure(path=outputDir, figure=sharedFigure)

        if show:
            plot.show(block=True)