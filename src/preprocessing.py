import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

def perform_pca(data_matrix, n_components=3):
    """Perform PCA on the data matrix."""
    # Scale the data
    scaled_data = StandardScaler().fit_transform(data_matrix)
    
    # Apply PCA
    pca = PCA(n_components=n_components)
    pca_result = pca.fit_transform(scaled_data)
    
    # Create results dataframe
    results_df = pd.DataFrame(
        data=pca_result, 
        columns=[f'PC{i+1}' for i in range(n_components)], 
        index=data_matrix.index
    )
    
    return results_df, pca 