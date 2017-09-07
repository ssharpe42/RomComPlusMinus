setwd('/Users/Sam/Desktop/Projects/ActorPlusMinus/')
options(stringsAsFactors = F)
library(dplyr)
library(readr)
library(tidyr)
library(ggplot2)
library(scales)
library(ggthemes)

#Load data
raw_data = read_csv('data/raw_data.csv')
all_actors = read.csv('data/all_results.csv')%>%
    filter(ActorIndicator==1) %>% select(Variable)
male_results = read.csv('data/male_results.csv') %>%
    filter(ActorAppear>=4) %>% rename(Male_Coef = Coef)
female_results = read.csv('data/female_results.csv')%>%
    filter(ActorAppear>=4)%>% rename(Female_Coef = Coef)
non_actor_data = read.csv('data/non_actor_data.csv')
topic_vec = read.csv('data/topic_vec.csv')

actors = male_results$Variable
actorsall = all_actors$Variable

#Gender Score Distributions
non_actor_data %>%
    select(female_score, male_score) %>%
    gather(Gender, Score) %>%
    mutate(Gender = ifelse(Gender=='female_score','Female','Male')) %>%
    ggplot()+
    geom_density(aes(x = Score, fill = Gender), alpha = .5)+
    scale_x_continuous(name = 'IMDb Rating')+
    theme_fivethirtyeight()+
    theme(axis.title = element_text(),
          axis.text.y = element_blank(),
          axis.title.y = element_blank())+
    ggtitle("Male vs. Female IMDb Ratings")

#Gender Score Distributions by content rating
non_actor_data %>%
    select(female_score, male_score,content_rating) %>%
    gather(Gender, Score, -content_rating) %>%
    mutate(Gender = ifelse(Gender=='female_score','Female','Male')) %>%
    ggplot()+
    geom_density(aes(x = Score, fill = Gender), alpha = .5)+
    facet_wrap(~content_rating)+
    scale_x_continuous(name = 'IMDb Rating')+
    theme_fivethirtyeight()+
    theme(axis.title = element_text(),
          axis.text.y = element_blank(),
          axis.title.y = element_blank())+
    ggtitle("Content Ratings Matter to Men")

#Rating vs Budget
lm_eqn <- function(df, x, y){
    m <- lm(df[,y] ~ df[,x]);
    format(summary(m)$r.squared, digits = 3)               
}
non_actor_data%>%
    ggplot(aes(x = budget, y = imdbscore))+
    geom_point() +
    stat_smooth(method = 'lm')+
    scale_x_continuous(label = function(x) paste0(dollar_format()(x/1e6),'M'), name = 'Budget')+
    scale_y_continuous(name = 'IMDb Rating')+
    theme_fivethirtyeight()+
    theme(axis.title = element_text())+
    geom_text(x = 75e6, y = 4.2, label = paste('Rsq =',lm_eqn(non_actor_data, 'imdbscore','budget')))+
    ggtitle("Budget Shmuget")
#p + geom_text(x = 75e6, y = 4.2, label = lm_eqn(non_actor_data), parse = T)
#Rating vs time
non_actor_data%>%
    ggplot(aes(x = time, y = imdbscore))+
    geom_point() +
    stat_smooth(method = 'lm')+
    scale_x_continuous( name = '\nMovie Time', label = function(x) paste0(floor(x/60),' hrs\n',x %% 60 ,' min'))+
    scale_y_continuous(name = 'IMDb Rating')+
    theme_fivethirtyeight()+
    theme(axis.title = element_text())+
    geom_text(x = 120, y = 4.2, label = paste('Rsq =',lm_eqn(non_actor_data, 'imdbscore','time')))+
    ggtitle("Is Longer Better?", subtitle = 'Movie Run Times vs. IMDb Ratings')

#Rating vs votes
non_actor_data%>%
    mutate(votes = log10(exp(votes)))%>%
    ggplot(aes(x = votes, y = imdbscore))+
    geom_point() +
    stat_smooth(method = 'lm')+
    scale_x_continuous( name = '\nIMDb Votes', label = function(x) paste0(10,'^',x))+
    scale_y_continuous(name = 'IMDb Rating')+
    theme_fivethirtyeight()+
    theme(axis.title = element_text())+
    geom_text(x = log10(2e5), y = 4.2, label = paste('Rsq =',lm_eqn(non_actor_data, 'imdbscore','votes')))+
    ggtitle("Voting: The First Sign of Approval")


#Top 10 All Results
compare = left_join(male_results %>% select(Male_Coef, Variable), 
              female_results %>% select(Female_Coef, Variable)) %>%
    mutate(AvgScore = (Male_Coef+Female_Coef)/2,
            Male_Rank =dense_rank(desc(Male_Coef)),
           Female_Rank = dense_rank(desc(Female_Coef)),
           Rank = dense_rank(desc(AvgScore)))
        
#Write for table
write.csv( select(compare, `Actor/Actress` = Variable, 
                                  `Female RC-PM`= Female_Coef, 
                                  `Male RC-PM`= Male_Coef) %>%
              mutate(Overall = round((`Female RC-PM`+`Male RC-PM`)/2,3),
                     `Female RC-PM`= round(`Female RC-PM`, 3),
                     `Male RC-PM` = round(`Male RC-PM`, 3)), 
           'All RC-PM.csv',row.names = F)

#Prepare Scores for Top and Bottom 10 Actors
Scores = compare%>%
    arrange(-AvgScore)%>%
    mutate(Class = factor(ifelse(row_number()<=10,'Top 10','Bottom 10'),levels = c('Top 10','Bottom 10'), ordered = T),
           Variable = paste0(row_number(),'. ', Variable))%>%
    filter(row_number()<=10|row_number() >= n()-9)%>%
    select(Variable, Male_Coef, Female_Coef, AvgScore, Class)%>%
    gather(Gender, Score, -Variable,-Class) %>%
    mutate(Gender = ifelse(Gender =='AvgScore','Overall', 
                           ifelse(Gender=='Male_Coef','Male','Female')),
           Variable = factor(Variable, levels = rev(Variable), ordered = T)) %>%
    group_by(Variable) %>%
    mutate(Min= min(Score), Max  = max(Score)) %>%ungroup

#Top and Bottom Ten RC-PM
ggplot(Scores)+
    geom_errorbar(aes(ymin = Min, ymax = Max, x = Variable), width = .1, linetype = 'dotted')+
    geom_point(aes(y = Score, x = Variable, colour = Gender),size=3)+
    scale_color_manual(values = c('Female'='#F8766D','Male'='#00BFC4','Overall' = 'black'))+
    coord_flip()+
    facet_wrap(~Class, scales = 'free')+
    theme_fivethirtyeight()+
    scale_y_continuous(name = 'Romcom Plus-Minus (RC-PM)')+
    scale_x_discrete(name='Actor/Actress')+
    theme(axis.title = element_text(),
          axis.line = element_blank()) +
    ggtitle("Top/Bottom 10 Actors According to RC-PM")




#Compare PM distributions
compare %>%
    gather(Gender, PlusMinus, -matches('Rank|Varia')) %>%
    mutate(Gender = ifelse(Gender =='Coef','Overall', 
                           ifelse(Gender=='Male_Coef','Male','Female'))) %>%
    ggplot()+
    geom_density(aes(x = PlusMinus, fill = Gender), alpha = .5)


# Plot Topics
ggplot(non_actor_data,aes(x = Topic0, y = Topic1)) +
    #geom_point( size = 3, alpha = .3)+
    geom_text(aes(label = movie), alpha = .3)+
    theme(axis.text = element_blank(),
          axis.ticks = element_blank())

ggplot(non_actor_data %>% filter(movie %in% 
                                     c("She's All That","Easy A","Sixteen Candles",
                                       "10 Things I Hate About You",'The Girl Next Door',
                                       "John Tucker Must Die",
                                       "Bride Wars","Bachelorette","27 Dresses") | grepl('Wedding',movie)),
       aes(x = Topic0, y = Topic1)) +
    #geom_point( size = 3, alpha = .3)+
    geom_text(aes(label = movie))+
    xlim(c(-.27,-.1))+
    theme_fivethirtyeight()+
    theme(axis.text = element_blank(),
          axis.ticks = element_blank())


