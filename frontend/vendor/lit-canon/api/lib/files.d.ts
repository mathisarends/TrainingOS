export declare function isWithin(parent: string, child: string): boolean;
export declare function listFiles(root: string, preserveDirectories?: ReadonlySet<string>): Promise<Map<string, string>>;
export declare function hasErrorCode(error: unknown, code: string): boolean;
export declare function outputFiles(output: string, preserveDirectories?: ReadonlySet<string>): Promise<Map<string, string>>;
