# @TODO Dynamically filter peptide set based on length(s) of input sequences of binders
#       i.e. 2 binders, one 11 AA long, one 13 AA long, each gets their own "subset" of the
#       full peptide lilst that can be compared to it. For any number of input sequences

# @TODO implement method for both similarities to M6 and GrBP5 to interrelate and act as their own feature set:
# i.e. if a peptide matches both peptides in temrs of sequence at some index, that should be important rather than
# having it equal to one matching only one

# @TODO: Maybe as originally planned implement binders inputted as dictionary of multiple values, each with separate
#      dataframes within the same class --> for big similarity calculations. Or just create multiple SequenceSimilarity instances

import pandas as pd
import numpy as np
from scipy.stats import kendalltau
import matplotlib.pyplot as plt
from typing import Set, Tuple, Dict, List

class SequenceSimilarity:
    '''
    Class that takes in a path to a list of amino acid sequences as well
    as any number of peptide sequences explicitly that are known to have
    a certain set of properties. Generates metrics for similarity for each
    peptide in path and returns domains AA sequence with high similarity
    '''

    def __init__(self, binder: str,   
                 data_paths: Dict,     #@TODO Make another .py file containing object version of necessary sim matrices/conversions, etc.
                 peps_path: str,       #      to reduce reliance on outside data
                 aa_col: str):         #-> The column in peps_path csv where sequences are held
        
        self.AA = set('LINGVEPHKAYWQMSCTFRD')
        self.EIIP = [0,0,0.0036,0.005,0.0057,0.0058,0.0198,0.0242,0.0371,0.0373,0.0516,0.0548,0.0761,0.0823,0.0829,0.0829,0.0941,0.0946,0.0959,0.1263]
        self.AA_EIIP = dict(zip(self.AA, self.EIIP)) #this and field above might be extraneous with data['AA_map'], or vice versa?
        # @TODO find which lookup is faster: dict or df.values and implement
        
        self.binder = binder   # to get binder_len, just use len(self.binders)
        self.__read_similarity_data(data_paths)

        self.aa_col = aa_col
        self.columns = ['EIIP_Seq', 'Num_Seq', 'PAM30', 'BLOSUM', 'RRM_SN', 'RRM_Corr']
        ## @TODO: Add "# of matching sseqs, cross entropy AA, cross entropy Num columns ?"
        
        self.peps = pd.read_csv(peps_path)
        self.peps.columns = [aa_col]
        self.peps_same_len = self.peps[self.peps[aa_col].str.len() == len(binder)]
        if len(self.peps_same_len) == 0:
            raise Exception("No peptides of same length as binder found")
        self.peps_sl_sim = self.peps_same_len.copy()
        print(self.peps_sl_sim)
        for col in self.columns:
            self.peps_sl_sim[col] = None
        
        #self.get_similarities()

    def __read_similarity_data(self, data_path_dict) -> None:
        """
        Private method to store the paths of any data needed
        for similarity calcs and create Dataframes from them
        """
        self.data = dict.fromkeys(data_path_dict.keys())
        for data in data_path_dict.keys():
            if data == "AA_MAP":
                self.data[data] = pd.read_csv(data_path_dict[data])
            else:
                self.data[data] = pd.read_csv(data_path_dict[data], index_col=0)

    def _get_AA_conversion(self, conv_type: str = None) -> None:
        AA_map = self.data["AA_MAP"][['AA', conv_type ]]
        def get_aa_conv(pep):
            new_seq = list()
            for AA in pep:
                if AA not in self.AA:
                    val = 0
                else:
                    val = AA_map.loc[AA_map['AA']==AA][conv_type].values[0]
                new_seq.append(val)
            return new_seq
        # get_aa_conv = lambda pep: map(lambda aa: AA_map.loc[AA_map['AA']==aa][conv_type].values[0], pep)
        self.peps_sl_sim[conv_type+"_Seq"] = self.peps_sl_sim[self.aa_col].apply(get_aa_conv)

    def _get_PAM30_similarity(self) -> pd.DataFrame:
        pass

    def _get_BLOSUM_similarity(self) -> pd.DataFrame:
        pass

    def _get_RRM_SN_similarity(self) -> None:
        pass

    def _get_RRM_corr_similarity(self) -> None:
        pass

    def _get_matching_sseqs(self):
        pass
    
    def get_similarities(self) -> None:
        self._get_AA_conversion(conv_type='EIIP')
        self._get_AA_conversion(conv_type='Num')
        self._get_BLOSUM_similarity()
        self._get_PAM30_similarity()
        self._get_RRM_SN_similarity()
        self._get_RRM_corr_similarity()
        self._get_matching_sseqs()

    def df_filter_subseq(self, sub_seq: str, ind: int = None) -> pd.DataFrame:
        '''
        Takes in a subsequence of equal or lesser length to
        peptides in class peptide dataframe and returns a dataframe
        containing only those peptides containing the sequence
        '''
        if not {*sub_seq}.issubset({*self.AA}):
            raise Exception('Invalid subsequence')
        if ind is None:
            return self.peps_sl_sim[self.peps_sl_sim[self.aa_col].str.contains(sub_seq)]
        return self.peps_sl_sim[self[self.peps_sl_sim[self.aa_col].str.find(sub_seq) == ind]]

    def get_sim_matrix(self, seq) -> pd.DataFrame:
        return self.data.filter

    def get_binder_subseq(self) -> Dict[str, List[Tuple[str, int]]]: #Each binder associated with list of (sseq, index)
        '''
        Generates all possible subsequences for binders. Returns in dict, where
        each binder corresponds to a dictionary of the index where it occurs,
        and the subsequence that occurs
        '''
        return [(s[i:j], i) for i in range(len(s)) for j in range(i+1, len(s)+1)]


    def get_df_with_binder_subseqs(self, min_length: int = 0) -> Dict[str, pd.DataFrame]:
        '''
        Returns a filtered version of self.peps_same_len DataFrame containing only
        those rows with sequences which contain subsequences (of min length specified in parameter) 
        of the two binder sequences in the locations where they occur in the binders
        '''
        sseq = self.get_binder_subseq()
        filtered_data = [self.df_fitler_subseq(ss,i) for (ss,i) in sseq[binder] if len(ss) >= min_length]
        data = pd.concat(filtered_data)
        return data

    def get_kendalltau_corr_map(self) -> Tuple:
        return kendalltau(self.data['AA_MAP'][['Num']], self.data['AA_MAP'][['EIIP']])